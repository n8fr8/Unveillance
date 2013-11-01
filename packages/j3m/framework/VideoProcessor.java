package framework;

import java.io.File;
import java.security.NoSuchAlgorithmException;

import util.Util;

import ffmpeg.FfmpegException;
import ffmpeg.FfmpegWrapper;

public class VideoProcessor extends FileProcessor{
	
	
	
	public VideoProcessor(File sourceFile, File outputFolder) {
		super(sourceFile, outputFolder);
	}
	public void processMetadata() throws FfmpegException, Exception{
		File outFile = new File(getOutputFolder(),
						getSourceFileName() + "." + 
						FrameworkProperties.getInstance().getVideoMetadataFileExt());
		FfmpegWrapper ffmpeg = new FfmpegWrapper();
		ffmpeg.extractMetadata(getSourceFile(), outFile);
		
		J3mMetadataProcessor metadataProcessor = new J3mMetadataProcessor(outFile,getOutputFolder());
		metadataProcessor.processMetadata();
		
		//
		
	}
	
	
	public void createStillAndThumbnail() throws FfmpegException, Exception{
		File stillFile = new File(getOutputFolder(),
		Util.getBaseFileName(getSourceFile()) + "." + 
		FrameworkProperties.getInstance().getVideoStillFileExt());
		FfmpegWrapper ffmpeg = new FfmpegWrapper();
		try {
			ffmpeg.createStill(getSourceFile(), stillFile);
		} catch (Exception e) {
			throw new FfmpegException("Still file " + stillFile + " could not be created", e);
		}
		File thumbFile = new File(getOutputFolder().getAbsolutePath(),
		"thumb_" + getSourceFileName() + "." + 
		FrameworkProperties.getInstance().getThumbFileExt());
		try {
			Util.resizeImage(stillFile, thumbFile, 
					FrameworkProperties.getInstance().getThumbWidth(), 
					FrameworkProperties.getInstance().getThumbHeight());
		} catch (Exception e) {
			throw new Exception("Thumbnail file " + thumbFile + " could not be created", e);
		}
	}

	public void toLowResolution(boolean updateSource)throws Exception{
		File outFile = new File (getOutputFolder(),
		"low_" + getSourceFileName() + "." + 
		Util.getFileExtenssion(getSourceFile()));
		try {
			FfmpegWrapper ffmpeg = new FfmpegWrapper();
			ffmpeg.changeResolution(getSourceFile(), outFile, 
					FrameworkProperties.getInstance().getVideoSmallWidth(), 
					FrameworkProperties.getInstance().getVideoSmallHeight());
			if (updateSource) {
				setSourceFile(outFile);
			}
			// create an ogv version
			ffmpeg.convertToOgv(outFile);
		} catch (Exception e) {
			throw new Exception("Low res video file " + outFile + " could not be created", e);
		}
		
	}
	public void toMediumResolution(boolean updateSource)throws Exception{
		File outFile = new File(getOutputFolder(),
		"med_" + getSourceFileName() + "." +
		Util.getFileExtenssion(getSourceFile()));
		try {
			FfmpegWrapper ffmpeg = new FfmpegWrapper();
			ffmpeg.changeResolution(getSourceFile(), outFile, 
					FrameworkProperties.getInstance().getVideoMedWidth(), 
					FrameworkProperties.getInstance().getVideoMedHeight());
			if (updateSource) {
				setSourceFile(outFile);
			}
			// create an ogv version
			ffmpeg.convertToOgv(outFile);
		} catch (Exception e) {
			throw new Exception("Medium res video file " + outFile + " could not be created", e);
		}
		
	}
	public void toHighResolution(boolean updateSource) throws Exception{
		File outFile = new File(getOutputFolder().getAbsolutePath() ,
		"high_" + getSourceFileName() + "." + 
		Util.getFileExtenssion(getSourceFile()));
		try {
			FfmpegWrapper ffmpeg = new FfmpegWrapper();
			ffmpeg.changeResolution(getSourceFile(), outFile, 
					FrameworkProperties.getInstance().getVideoLargeWidth(), 
					FrameworkProperties.getInstance().getVideoLargeHeight());
			if (updateSource) {
				setSourceFile(outFile);
			}
			// create an ogv version
			ffmpeg.convertToOgv(outFile);
		} catch (Exception e) {
			throw new Exception("High res video file " + outFile + " could not be created", e);
		}
	}
	
	public void toOriginalResolution(boolean updateSource) throws Exception{
		File outFile = new File(getOutputFolder().getAbsolutePath(),
				getSourceFileName() + "." + FrameworkProperties.getInstance().getVideoConvertedFormat()); 
		
		try {
			FfmpegWrapper ffmpeg = new FfmpegWrapper();
			ffmpeg.changeFormat(getSourceFile(), outFile);
			if (updateSource) {
				setSourceFile(outFile);
			}
			// create an ogv version
			ffmpeg.convertToOgv(outFile);
		} catch (Exception e) {
			throw new Exception("Reformatted video file " + outFile + " could not be created", e);
		}
	}
	
	public String getVideoHash() throws FfmpegException, NoSuchAlgorithmException {
		FfmpegWrapper ffmpeg = new FfmpegWrapper();
		String md5 = ffmpeg.getVideoRgbMd5(getSourceFile());
		return Util.saltAndHash(md5, FrameworkProperties.getInstance().getSalt());
		
	}
	
	public String getAudioHash() throws FfmpegException, NoSuchAlgorithmException {
		FfmpegWrapper ffmpeg = new FfmpegWrapper();
		String md5 = ffmpeg.getAudioMd5(getSourceFile());
		return Util.saltAndHash(md5, FrameworkProperties.getInstance().getSalt());
		
	}
}
