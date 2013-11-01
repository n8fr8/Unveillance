package framework;

import j3m.J3MException;
import j3m.J3MWrapper;

import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;

import javax.imageio.ImageIO;
import util.Util;



public class ImageProcessor extends FileProcessor{
	
	private int originalWidth = 0;
	private int originalHeight = 0;
	
	public ImageProcessor(File sourceFile, File outputFolder)throws Exception {
		super(sourceFile, outputFolder);
		try {
			BufferedImage bimg = ImageIO.read(sourceFile);
			originalWidth          = bimg.getWidth();
			originalHeight         = bimg.getHeight();
		} catch (IOException e) {
			FrameworkProperties.processError("Could not get image dimenssions", e);
		}
	}

	public void processMetadata() throws J3MException, Exception{
		File outFile = new File(getOutputFolder(),
		getSourceFileName() + "." +
		FrameworkProperties.getInstance().getImageMetadataFileExt());
		J3MWrapper j3m = new J3MWrapper();
		j3m.extractMetaData(getSourceFile(), outFile);
		
		J3mMetadataProcessor metadataProcessor = new J3mMetadataProcessor(outFile,getOutputFolder());
		metadataProcessor.processMetadata();
	}
	
	public void createThumbnail() throws Exception{
		File outFile = new File(getOutputFolder(), "thumb_" + getSourceFileName() + "." + 	
		FrameworkProperties.getInstance().getThumbFileExt());
		try {
			Util.resizeImage(getSourceFile(), outFile, 
					FrameworkProperties.getInstance().getThumbWidth(), 
					FrameworkProperties.getInstance().getThumbHeight());
		} catch (Exception e) {
			throw new Exception("Thumbnail file " + outFile.getName() + " could not be created", e);
		}
		
	}
	public void toLowResolution(boolean updateSource) throws Exception{
		File outFile = new File(getOutputFolder(),
		"low_" + getSourceFileName() + "." + 
		Util.getFileExtenssion(getSourceFile()));
		try {
			int width = FrameworkProperties.evaluateDemension(FrameworkProperties.getInstance().getImageSmallWidth(), originalWidth);
			int height = FrameworkProperties.evaluateDemension(FrameworkProperties.getInstance().getImageSmallHeight(), originalHeight);
			Util.resizeImage(getSourceFile(), outFile, width, height);
			if (updateSource) {
				setSourceFile(outFile);
			}
		} catch (Exception e) {
			throw new Exception("Low res image file " + outFile.getName() + " could not be created", e);
		}
	}
	public void toMediumResolution(boolean updateSource)throws Exception{
		File outFile = new File(getOutputFolder(),
		"med_" + getSourceFileName() + "." + 
		Util.getFileExtenssion(getSourceFile()));
		try {
			int width = FrameworkProperties.evaluateDemension(FrameworkProperties.getInstance().getImageMedWidth(), originalWidth);
			int height = FrameworkProperties.evaluateDemension(FrameworkProperties.getInstance().getImageMedHeight(), originalHeight);
			Util.resizeImage(getSourceFile(), outFile, width, height);
			if (updateSource) {
				setSourceFile(outFile);
			}
		} catch (Exception e) {
			throw new Exception("Medium res image file  " + outFile.getName() + " could not be created", e);
		}
		
	}
	public void toHighResolution(boolean updateSource)throws Exception{
		File outFile = new File(getOutputFolder(),
		"high_" + getSourceFileName() + "." + 
		Util.getFileExtenssion(getSourceFile()));
		try {
			int width = FrameworkProperties.evaluateDemension(FrameworkProperties.getInstance().getImageLargeHeight(), originalWidth);
			int height = FrameworkProperties.evaluateDemension(FrameworkProperties.getInstance().getImageLargeHeight(), originalHeight);
			Util.resizeImage(getSourceFile(), outFile, width, height);
			if (updateSource) {
				setSourceFile(outFile);
			}
		} catch (Exception e) {
			throw new Exception("High res image file " + outFile.getName() + " could not be created", e);
		}
		
	}
	public void toOriginalResolution(boolean updateSource)throws Exception{
		File outFile =  new File(getOutputFolder(), getSourceFile().getName());
		try {
			BufferedImage image = ImageIO.read(getSourceFile());
			String fileType = Util.getFileExtenssion(outFile);
			ImageIO.write(image, fileType, outFile);
			if (updateSource) {
				setSourceFile(outFile);
			}
		} catch (Exception e) {
			throw new Exception("Image file " + outFile.getName() + " could not be created", e);
		}
		
	}

}
