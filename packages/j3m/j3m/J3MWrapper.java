package j3m;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.List;

import org.apache.commons.io.FileUtils;

import util.CommandRunner;
import util.StreamToFile;
import util.Util;
import framework.FrameworkProperties;


/**
 * Wrapper for the command line untility that extract j3m metadata from image files 
 * @author NB
 *
 */
public class J3MWrapper {
	public void extractMetaData(File inputFile, File outputFile ) throws J3MException{
		FrameworkProperties config = FrameworkProperties.getInstance();
		String command = Util.replaceFileMarkers(config.getJ3MGetMetadata(), inputFile.getAbsolutePath(), outputFile.getAbsolutePath() );
		try {
			StreamToFile streamProcessor = new StreamToFile(outputFile);
			CommandRunner commandRunner = new CommandRunner();
            commandRunner.runCommand(command, streamProcessor);
            cleanFile(outputFile);
				
		} catch (Exception e) {
			throw new J3MException("Could not run the j3mParser command???: " + command, e);
		} 

	}
	
	public void cleanFile(File inputFile)throws Exception {
		BufferedReader reader = new BufferedReader(new FileReader(inputFile));
		String line = "";
		//skip past the lines to be ignored
		List<String> ignoreLines = FrameworkProperties.getInstance().getJ3MIgnoreLines();
		boolean skipping = true;
		while (skipping) {
			line = reader.readLine();
			FrameworkProperties.processMessage(line);
			skipping = false;
			for(String l: ignoreLines){
				if(line.matches(l)){
					skipping = true;
				}
			}
			
		}
		File temp = new File(inputFile.getParent(), inputFile.getName() + ".temp");
		BufferedWriter writer = new BufferedWriter(new FileWriter(temp));
		while(line != null) {
			writer.write(line);
			line = reader.readLine();
		}
		writer.close();
		FileUtils.copyFile(temp,inputFile);
		if (!FrameworkProperties.getInstance().getDebug()){
			temp.delete();
		}
	}
}
