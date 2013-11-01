package gpg;


import framework.FrameworkProperties;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.List;

import util.CommandRunner;
import util.StreamToStdOut;
import util.StreamToString;
import util.Util;

public class GPGWrapper {

	public boolean verifySignature(File signedData, File signatureFile) throws GPGException{
		FrameworkProperties config = FrameworkProperties.getInstance();
		StreamToString streamProcessor = new StreamToString(null);
		List<String> files = new ArrayList<String>();
		files.add(signatureFile.getAbsolutePath());
		files.add(signedData.getAbsolutePath());
		String command = Util.replaceMarkers(config.getGpgVerifySignature(), "file", files);
		try {
			CommandRunner commandRunner = new CommandRunner();
            commandRunner.runCommand(command, streamProcessor);
		    if (streamProcessor.getResult() != null && streamProcessor.getResult().contains(config.getGpgSignatureOK())) {
		    	return true;
		    }
		} catch (Exception e) {
			throw new GPGException("Could not run command: " + command, e);
		} 
		return false;
	}
	
	public void decrypt(File sourceFile, File outputFile)throws GPGException {
		FrameworkProperties config = FrameworkProperties.getInstance();
		
		String command = Util.replaceFileMarkers(config.getGpgDecrypt(), sourceFile.getAbsolutePath(), outputFile.getAbsolutePath() );
		try {
			StreamToStdOut streamProcessor = new StreamToStdOut();
			CommandRunner commandRunner = new CommandRunner();
			File password = new File(config.getGpgPassword());
			BufferedReader reader = new BufferedReader(new FileReader(password));
			StringBuilder stringBuilder = new StringBuilder(reader.readLine());
            commandRunner.runCommand(command, streamProcessor,stringBuilder);
				
		} catch (Exception e) {
			throw new GPGException("Could not run command: " + command, e);
		} 
	}
}
