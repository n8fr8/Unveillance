package tests;

import java.io.File;

import org.junit.Assert;
import org.junit.Test;

import util.Util;

import framework.FrameworkProperties;
import framework.ImageProcessor;

public class ImageProcessorTest {
	FrameworkProperties config = FrameworkProperties.getInstance();
	TestProperties testConfig = TestProperties.getInstance();

	@Test
	public void createThumbnailTest() throws Exception {
		ImageProcessor imageProcessor = new ImageProcessor(new File(testConfig.getTestImage()), new File(testConfig.getOutputFolder()));
		String outFile = testConfig.getOutputFolder()+ "thumb_" + Util.getBaseFileName(testConfig.getTestImage()) + "." + config.getThumbFileExt();
		long timestamp = System.currentTimeMillis();
		imageProcessor.createThumbnail();
		File outputFile = new File(outFile);
		if (!outputFile.exists()){
		    Assert.fail("Thumbnail image file " + outputFile.getPath() + " does not exist");
		}
		Assert.assertTrue("Thumbnail image file timestamp doesnt reflect operation", timestamp < outputFile.lastModified());
	}
	
	@Test
	public void toLowResolutionTest() throws Exception {
		ImageProcessor imageProcessor = new ImageProcessor(new File(testConfig.getTestImage()), new File(testConfig.getOutputFolder()));
		String outFile = testConfig.getOutputFolder()+ "low_" + Util.getBaseFileName(testConfig.getTestImage()) + "." + config.getThumbFileExt();
		long timestamp = System.currentTimeMillis();
		imageProcessor.toLowResolution(false);
		File outputFile = new File(outFile);
		if (!outputFile.exists()){
		    Assert.fail("Low res image file " + outputFile.getPath() + " does not exist");
		}
		Assert.assertTrue("Low res image file timestamp doesnt reflect operation", timestamp < outputFile.lastModified());
	}
	
	@Test
	public void toMediumResolutionTest() throws Exception {
		ImageProcessor imageProcessor = new ImageProcessor(new File(testConfig.getTestImage()), new File(testConfig.getOutputFolder()));
		String outFile = testConfig.getOutputFolder()+ "med_" + Util.getBaseFileName(testConfig.getTestImage()) + "." + config.getThumbFileExt();
		long timestamp = System.currentTimeMillis();
		imageProcessor.toMediumResolution(false);
		File outputFile = new File(outFile);
		if (!outputFile.exists()){
		    Assert.fail("Medium res image file " + outputFile.getPath() + " does not exist");
		}
		Assert.assertTrue("Medium res image file timestamp doesnt reflect operation", timestamp < outputFile.lastModified());
	}
	
	@Test
	public void toHighResolutionTest() throws Exception {
		ImageProcessor imageProcessor = new ImageProcessor(new File(testConfig.getTestImage()), new File(testConfig.getOutputFolder()));
		String outFile = testConfig.getOutputFolder()+ "high_" + Util.getBaseFileName(testConfig.getTestImage()) + "." + config.getThumbFileExt();
		long timestamp = System.currentTimeMillis();
		imageProcessor.toHighResolution(false);
		File outputFile = new File(outFile);
		if (!outputFile.exists()){
		    Assert.fail("High res file " + outputFile.getPath() + " does not exist");
		}
		Assert.assertTrue("Thumbnail image file timestamp doesnt reflect operation", timestamp < outputFile.lastModified());
	}
	
	@Test
	public void toOriginalResolutionTest() throws Exception {
		ImageProcessor imageProcessor = new ImageProcessor(new File(testConfig.getTestImage()), new File(testConfig.getOutputFolder()));
		String outFile = testConfig.getOutputFolder()+ Util.getBaseFileName(testConfig.getTestImage()) + "." + config.getThumbFileExt();
		long timestamp = System.currentTimeMillis();
		imageProcessor.toOriginalResolution(true);
		File outputFile = new File(outFile);
		if (!outputFile.exists()){
		    Assert.fail("Original res image file " + outputFile.getPath() + " does not exist");
		}
		Assert.assertTrue("Original res image file timestamp doesnt reflect operation", timestamp < outputFile.lastModified());
	}
	
	
	
	
	
	
	
	
}
