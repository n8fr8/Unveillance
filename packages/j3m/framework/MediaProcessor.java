package framework;

import java.io.File;


import util.Util;


public class MediaProcessor {
	
	public static void main(String[] args){
		try {
			MediaProcessor processor = new MediaProcessor();
			processor.processInput(args);
		} catch (Exception e) {
			System.err.println("Error occured: \n" + e.getMessage());
			System.out.println("Please provide arguments in the format: <source file> <output folder>");
			System.exit(1);
		}
	}

	public void processInput(String[] args) throws Exception{
		String sourceFile = args[0];
		String destinationFolder = args[1];
		
		//null pointer exceptions will be caught in the main catch all
		//input validation:
		File source;
		File destination;
		try {
			source = new File(sourceFile);
			destination = new File(destinationFolder);
		} catch (NullPointerException e) {
			throw new Exception("Empty argument", e);
		}
		if (!source.exists()) {
			throw new Exception("Source '" + sourceFile  + "' does not exist");
		}
		if (!source.isFile()) {
			throw new Exception("Source '" + sourceFile  + "' is not a file");	
		}
		if (!destination.exists()) {
			throw new Exception("Destination '" + destinationFolder  + "' does not exist");
		}
		if (!destination.isDirectory()) {
			throw new Exception("Destination '" + destinationFolder  + "' is not a directory");
		}
		
		//process optional parameters, if they are unknown, just ignore them
		int varCount = 2;
		boolean keepLooking = true;
		boolean metadataOnly = false;
		while(keepLooking) {
			if (args.length > varCount){
				String optionalPramater = args[varCount];
				if ("-v".equals(optionalPramater)) {
					FrameworkProperties.getInstance().setVerbose(true);
					System.out.println("verbose mode switched on");
				}else if ("-l".equals(optionalPramater)) {
					FrameworkProperties.getInstance().setLenient(true);
					System.out.println("lenient mode switched on");
				}else if ("-m".equals(optionalPramater)) {
					System.out.println("treating input file as metadata only");
					metadataOnly = true;
				}else if ("-d".equals(optionalPramater)) {
					System.out.println("debug mode switched on");
					FrameworkProperties.getInstance().setDebug(true);
				}else {
					System.out.println("Unknown paramter " + optionalPramater);
					System.out.println("Supported optional paramters are -v and -l");
				}
				varCount++;
			}else {
				keepLooking = false;
			}
		}
		
		
		//figure out what it is and do the actual work
		FrameworkProperties config = FrameworkProperties.getInstance();
		String fileType;
		try {
			fileType = Util.getFileExtenssion(source).toLowerCase();
		} catch (Exception e) {
			throw new Exception("Source '" + sourceFile  + "' is not in one of accepted formats : " + config.getImageInputTypesString() + " or " + config.getVideoInputTypesString(), e );
		}
		if (config.getImageInputTypes().contains(fileType)) {
			processImage(source,destination);
		}else if (config.getVideoInputTypes().contains(fileType)) {
			processVideo(source,destination);
		}else if (metadataOnly){
			J3mMetadataProcessor metadataProcessor = new J3mMetadataProcessor(source,destination);
			metadataProcessor.processMetadata();
		}else {
			throw new Exception("Source '" + sourceFile  + "' is not in one of accepted formats : " + config.getImageInputTypesString() + " or " + config.getVideoInputTypesString() );
		}

	}

	private void processVideo(File sourceFile, File outputFolder) throws Exception {
		VideoProcessor video = new VideoProcessor(sourceFile, outputFolder);
		try {
			try {
				video.processMetadata();
			} catch (Exception e) {
				FrameworkProperties.processError("Could not process metadata", e);
			}
			video.toOriginalResolution(true);
			video.createStillAndThumbnail();
			
			video.toLowResolution(false);
			video.toMediumResolution(false);
			video.toHighResolution(false);

		} catch (Exception e) {
			throw new Exception ("Error durring video processing: " + e.getLocalizedMessage(), e);
		}
	}

	private void processImage(File sourceFile, File outputFolder) throws Exception{
		ImageProcessor image = new ImageProcessor(sourceFile, outputFolder);
		try {
			try {
				image.processMetadata();
			} catch (Exception e) {
				FrameworkProperties.processError("Could not process metadata", e);
			}
			image.toOriginalResolution(true);
			image.createThumbnail();
			
			image.toLowResolution(false);
			image.toMediumResolution(false);
			image.toHighResolution(false);

		} catch (Exception e) {
			throw new Exception ("Error durring image processing: " + e.getLocalizedMessage(), e);
		}
		
	}
}
