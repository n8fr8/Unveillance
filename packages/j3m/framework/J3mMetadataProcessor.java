package framework;

import ffmpeg.FfmpegWrapper;
import gpg.GPGException;
import gpg.GPGWrapper;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.io.FileUtils;

import util.JSONTreeSearcher;
import util.Util;

import com.google.gson.stream.JsonWriter;

public class J3mMetadataProcessor extends FileProcessor{
	
	private List<File> fileTrail;

	public J3mMetadataProcessor(File sourceFile, File outputFolder) {
		super(sourceFile, outputFolder);
		fileTrail = new ArrayList<File>();
	}

	public void processMetadata() throws Exception{
		if (!JSONTreeSearcher.isJSON(getSourceFile())) {
			FrameworkProperties.processMessage("Starting JSONafication");
			toJSON();
		}
			
		try {
			procesGPGSignature();
		}catch (Exception e) {
			FrameworkProperties.processError("Failed to verify signature for file " + getSourceFile(), e);
		}
		
		File j3m = new File (getSourceFile().getParent(),  Util.getBaseFileName(getSourceFile()) + ".json");
		FileUtils.copyFile(getSourceFile(),j3m);
		fileTrail.add(getSourceFile());
		if (!FrameworkProperties.getInstance().getDebug()){
			for (File f : fileTrail){
				f.delete();
			}
		}
		setSourceFile(j3m);
		try {
			extractAudio();
		}catch (Exception e) {
			FrameworkProperties.processError("Failed to extract embedded audio " + getSourceFile(), e);
		}
		try {
			parseKeyWords();
		}catch (Exception e) {
			FrameworkProperties.processError("Failed to extract keywords " + getSourceFile(), e);
		}
	}
	
	/**
	 * As metadata files are zipped, maybe encrypted, and lastly base 64 encoded, 
	 * this method performs the reverse - base 64 decode, attempt decryption, 
	 * This method performs all neccessary operations in order to get the file into JSON format for further processing
	 * @param sourceFile
	 * @param outputFile
	 * @throws IOException
	 */
	public void toJSON() throws Exception{
		//decode
		File result = new File (getSourceFile().getParent(),  getSourceFile().getName() + ".from64");
		fileTrail.add(result);
		try {
			Util.decodeBase64File(getSourceFile(), result);
		} catch (Exception e) {
			FrameworkProperties.processError("Failed to base64 decode file " + getSourceFile(), e);
		}
		
		//check if it's encrypted
		BufferedReader reader = new BufferedReader(new FileReader(result));
		if (reader.readLine().contains("BEGIN PGP MESSAGE")){
			File encrypted = result;
			result = new File (getSourceFile().getParent(),  getSourceFile().getName() + ".decrypted");
			fileTrail.add(result);
			try {
				gpgDecrypt(encrypted, result );
			} catch (GPGException e) {
				FrameworkProperties.processError("Failed to decrypt file " + encrypted, e);
			}
		}
		
		//unzip
		File zipped = result;
		try {
			result = new File (getSourceFile().getParent(),  getSourceFile().getName() + ".unzipped");
			fileTrail.add(result);
			Util.unGzip(zipped, result);
			setSourceFile(result);
		} catch (Exception e) {		
			FrameworkProperties.processError("Failed to ungzip file " + zipped, e);
		}
	}
	
	
	
	public void gpgDecrypt(File sourceFile, File outputFile) throws GPGException{
		GPGWrapper gpgWrapper = new GPGWrapper();
		gpgWrapper.decrypt(sourceFile, outputFile);
	}
	
	
	public File extractAudio() throws Exception {
		File audioFile = null;
		JSONTreeSearcher jsonSearcher = new JSONTreeSearcher(getSourceFile(), FrameworkProperties.getInstance().getAudioContainer().split("\\."), true);
		jsonSearcher.performSearch();
		if (jsonSearcher.getEndElement()!= null) {
			// huston, we got audio
			audioFile = new File (getSourceFile().getParent(), getSourceFile().getName() + ".audio");
			FileWriter fw = new FileWriter(audioFile);
			fw.write(jsonSearcher.getEndElement().getAsString());
			fw.close();
			fileTrail.add(audioFile);
			
			//okie dokes, so we are expecting this file to be gziped, then b64 encoded, so iff we go in reverse weeeeeeeee
			try {
				File from64 = new File (getSourceFile().getParent(), getSourceFile().getName() + ".audio.fromb64");
				Util.decodeBase64File(audioFile, from64);
				fileTrail.add(from64);
				audioFile = from64;
			} catch (Exception e) {
				FrameworkProperties.processError("Failed to base64 decode file " + getSourceFile(), e);
			}
			
			//unzip
			try {
				File unZipped = new File (getSourceFile().getParent(),  Util.getBaseFileName(getSourceFile())  + "." + FrameworkProperties.getInstance().getAudioRawFormat());
				fileTrail.add(unZipped);
				Util.unGzip(audioFile, unZipped);
				audioFile = unZipped;
			} catch (Exception e) {		
				FrameworkProperties.processError("Failed to ungzip file " + audioFile, e);
			}
			// convert to a nicer format
			FfmpegWrapper ffmpeg = new FfmpegWrapper();
			try {
				File finalForm = new File (getSourceFile().getParent(),  Util.getBaseFileName(getSourceFile()) + "." + FrameworkProperties.getInstance().getAudioTargetFormat());
				
				ffmpeg.convertAudio(audioFile, finalForm);
				
				//alrighty then, all that said and done - update the JSON with path to file in place of raw data
				jsonSearcher.performSearchAndReplace(finalForm.getName());
				
				fw = new FileWriter(getSourceFile());
				fw.write(jsonSearcher.getJSON());
				fw.write("\n");//TODO move to preperties as an option
				fw.close();
				
			} catch (Exception e) {
				FrameworkProperties.processError("Failed to convert audio file " + audioFile, e);
			}
		}
		return audioFile;
	}
	
	
	/**
	 * Looks for a signature block as per the path provided in the propeties,
	 * if one is present, extracts it into a separate file and removes any charcater encoding
	 * Extracts the nested j3m data, and overwrites the  @param sourceFile
	 * @param sourceFile
	 * @return the File containing the signature
	 * @throws IOException 
	 */
	public File procesGPGSignature() throws IOException, GPGException, Exception {
		File sigFile = null;
		
		JSONTreeSearcher jsonSearcher = new JSONTreeSearcher(getSourceFile(), FrameworkProperties.getInstance().getSignatureContainer().split("\\."), true);
		jsonSearcher.performSearch();
		if (jsonSearcher.getEndElement()!= null) {
			// ok, we got a signature
			FrameworkProperties.processMessage("Found signature file");
			
			sigFile = new File (getSourceFile().getParent(), getSourceFile().getName() + ".sig");
			FileWriter fw = new FileWriter(sigFile);
			fw.write(jsonSearcher.getEndElement().getAsString());
			fw.close();
			
			//have to get the main j3m content out too
			jsonSearcher = new JSONTreeSearcher(getSourceFile(), FrameworkProperties.getInstance().getJ3mContainer().split("\\."), true);
			jsonSearcher.performSearch();
			if (jsonSearcher.getEndElement() != null) {
				File j3mFile = new File (getSourceFile().getParent(), getSourceFile().getName() +  ".json");
				
				//OK, because the JSONObject that was used to write the file does particular escapy stuff, and because the bytes
				// of that output were given to PGP, we can't let Java do any processing or escaping so just treat the file as bytes
				
				FileInputStream fis = new FileInputStream(getSourceFile());
				DataOutputStream os = new DataOutputStream( new FileOutputStream(j3mFile));
				byte[] buf = new byte[1024];
				try {
					int open = 0;
					int closed = -1;
					int offSet = new String("{\"" + FrameworkProperties.getInstance().getJ3mContainer() + "\":").getBytes().length;
					int readNum = fis.read(buf, 0, offSet);
					buf = new byte["}".getBytes().length];
		            while ((readNum = fis.read(buf)) != -1 && closed < open) {
		            	if( closed == -1) {
		            		//starting round
		            		closed = 0;	
		            	}
		            	if (Arrays.equals(buf,"}".getBytes())){
		            		closed++;
		            	}
		            	if (Arrays.equals(buf,"{".getBytes())){
		            		open++;
		            	}
		                os.write(buf, 0, readNum);
		            }

		        } catch (IOException ex) {
		            throw new IOException("Could not write j3m json file",ex);
		        }
		        os.close();
		        fis.close();
		        
		        setSourceFile(j3mFile);
		  
				GPGWrapper gpgWrapper = new GPGWrapper();

				if (!gpgWrapper.verifySignature(j3mFile, sigFile)) {
					throw new GPGException("Could not verify signature " + sigFile.getName() + " for file " + j3mFile.getName());
				}

			}else {
				//well, if we can't get the main j3m out, the signature wont verify, for one thing...'
				throw new GPGException("Could not find j3m data after GPG signature was found, for file " + getSourceFile().getName());
			}
		}
		return sigFile;
	}

	/**
	 * Uses google's gson lib to parse keywords out of metadata into a separate json file, probably badly
	 * this all seems very iffy and un-java-ry
	 * @param sourceFile
	 * @param outputFile
	 * @throws IOException
	 */
	public void parseKeyWords() throws IOException{
		File keyWordFile = new File (getOutputFolder(),
				"key_words_" + getSourceFileName() + "." + 
				FrameworkProperties.getInstance().getImageKeywordsFileExt());
		
		List<String> exclusions = FrameworkProperties.getInstance().getKeywordExclussions();
		List<String> keywordList = new ArrayList<String>();
		
		for (String container : FrameworkProperties.getInstance().getKeywordContainers()) {
			String[] path = container.split("\\.");
			JSONTreeSearcher jsonSearcher = new JSONTreeSearcher(getSourceFile(), path);
			List<String> values = jsonSearcher.performSearch();
			
			for (String value : values){
				if (value != null) {
					String[] keywords = value.toString().split(" ");
					for (int i = 0; i < keywords.length; i++) {
						if (!exclusions.contains(keywords[i])) {
							keywordList.add(keywords[i]);
						}
					}
				}
			}
		}
		JsonWriter jsonWriter;
		jsonWriter = new JsonWriter(new FileWriter(keyWordFile));
		jsonWriter.beginObject();
		jsonWriter.name("keywords");
		jsonWriter.beginArray();
		for (String keyword : keywordList) {
			jsonWriter.value(keyword);
		}
		jsonWriter.endArray();
		jsonWriter.endObject(); // }
		jsonWriter.close();
	}
}
