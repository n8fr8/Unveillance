package tests;

import java.io.File;

import org.junit.Assert;
import org.junit.Test;

import util.Util;
import framework.FrameworkProperties;
import framework.VideoProcessor;

public class VideoProcessorTests {
	
	FrameworkProperties config = FrameworkProperties.getInstance();
	TestProperties testConfig = TestProperties.getInstance();
	
	private VideoProcessor videoProcessor;
	
	
	public void setUP() {
		videoProcessor = new VideoProcessor(new File(testConfig.getTestVideo()), new File(testConfig.getOutputFolder()));
	}
	
	@Test
	public void runTests()throws Exception {
		setUP();
		toOriginalResolutionTest();
		createStillAndThumbnailTest();
		toHighResolutionTest();
		toMediumResolutionTest();
		toLowResolutionTest();
	}
	
	public void toOriginalResolutionTest() throws Exception{
		String outFile = testConfig.getOutputFolder()+ Util.getBaseFileName(testConfig.getTestVideo()) + "." + config.getVideoConvertedFormat() ;
		long timestamp = System.currentTimeMillis();
		videoProcessor.toOriginalResolution(true);
		File outputFile = new File(outFile);
		if (!outputFile.exists()){
		    Assert.fail("converted video file " + outputFile.getPath() + " does not exist");
		}
		Assert.assertTrue("converted video file timestamp doesnt reflect operation", timestamp < outputFile.lastModified());
		File ogvFile = new File (testConfig.getOutputFolder(), Util.getBaseFileName(testConfig.getTestVideo()) + ".ogv");
		if (!ogvFile.exists()){
		    Assert.fail("converted ogv video file " + ogvFile.getPath() + " does not exist");
		}
		Assert.assertTrue("converted ogv video file timestamp doesnt reflect operation", timestamp < ogvFile.lastModified());
	}
	
	
	public void createStillAndThumbnailTest() throws Exception {
		File stillFile =  new File(testConfig.getOutputFolder(),  Util.getBaseFileName(testConfig.getTestVideo()) + "." + config.getVideoStillFileExt());
		File thumbFile =  new File(testConfig.getOutputFolder(),  "thumb_" + Util.getBaseFileName(testConfig.getTestVideo()) + "." + config.getThumbFileExt());
		long timestamp = System.currentTimeMillis();
		videoProcessor.createStillAndThumbnail();
		if (!stillFile.exists()){
		    Assert.fail("Still video file " + stillFile.getPath() + " does not exist");
		}
		Assert.assertTrue("Still video file timestamp doesnt reflect operation", timestamp < stillFile.lastModified());
		if (!thumbFile.exists()){
		    Assert.fail("Thumb video file " + thumbFile.getPath() + " does not exist");
		}
		Assert.assertTrue("Thumb video file timestamp doesnt reflect operation", timestamp < thumbFile.lastModified());
	}
	
	public void toHighResolutionTest() throws Exception {
		String outFile = testConfig.getOutputFolder()+ "high_" + Util.getBaseFileName(testConfig.getTestVideo()) + "." + config.getVideoConvertedFormat();
		long timestamp = System.currentTimeMillis();
		videoProcessor.toHighResolution(true);
		File outputFile = new File(outFile);
		if (!outputFile.exists()){
		    Assert.fail("High res video file " + outputFile.getPath() + " does not exist");
		}
		Assert.assertTrue("High res video file timestamp doesnt reflect operation", timestamp < outputFile.lastModified());
		File ogvFile = new File (testConfig.getOutputFolder(),"high_" +  Util.getBaseFileName(testConfig.getTestVideo()) + ".ogv");
		if (!ogvFile.exists()){
		    Assert.fail("converted ogv video file " + ogvFile.getPath() + " does not exist");
		}
		Assert.assertTrue("converted ogv video file timestamp doesnt reflect operation", timestamp < ogvFile.lastModified());
	}
	

	public void toMediumResolutionTest() throws Exception {
		String outFile = testConfig.getOutputFolder()+ "med_" + Util.getBaseFileName(testConfig.getTestVideo()) + "." + config.getVideoConvertedFormat();
		long timestamp = System.currentTimeMillis();
		videoProcessor.toMediumResolution(false);
		File outputFile = new File(outFile);
		if (!outputFile.exists()){
		    Assert.fail("Medium res video file " + outputFile.getPath() + " does not exist");
		}
		Assert.assertTrue("Medium res video file timestamp doesnt reflect operation", timestamp < outputFile.lastModified());
		File ogvFile = new File (testConfig.getOutputFolder(), "med_" + Util.getBaseFileName(testConfig.getTestVideo()) + ".ogv");
		if (!ogvFile.exists()){
		    Assert.fail("converted ogv video file " + ogvFile.getPath() + " does not exist");
		}
		Assert.assertTrue("converted ogv video file timestamp doesnt reflect operation", timestamp < ogvFile.lastModified());
	}
	

	public void toLowResolutionTest() throws Exception {
		String outFile = testConfig.getOutputFolder()+ "low_" + Util.getBaseFileName(testConfig.getTestVideo()) + "." + config.getVideoConvertedFormat();
		long timestamp = System.currentTimeMillis();
		videoProcessor.toLowResolution(false);
		File outputFile = new File(outFile);
		if (!outputFile.exists()){
		    Assert.fail("Low res video file " + outputFile.getPath() + " does not exist");
		}
		Assert.assertTrue("Low res video file timestamp doesnt reflect operation", timestamp < outputFile.lastModified());
		File ogvFile = new File (testConfig.getOutputFolder(),"low_" +  Util.getBaseFileName(testConfig.getTestVideo()) + ".ogv");
		if (!ogvFile.exists()){
		    Assert.fail("converted ogv video file " + ogvFile.getPath() + " does not exist");
		}
		Assert.assertTrue("converted ogv video file timestamp doesnt reflect operation", timestamp < ogvFile.lastModified());
	}	
	
	@Test
	public void getHashTest() throws Exception {
		setUP();
		Assert.assertNotNull("No audio hash", videoProcessor.getAudioHash());
		Assert.assertEquals("Audion hash not repeatable", videoProcessor.getAudioHash(), videoProcessor.getAudioHash());
		
		Assert.assertNotNull("No video hash", videoProcessor.getVideoHash());
		Assert.assertEquals("Video hash not repeatable", videoProcessor.getVideoHash(), videoProcessor.getVideoHash());
	}
	
	@Test 
	public void processMetadatTest() throws Exception {
		VideoProcessor videoProcessor = new VideoProcessor(new File(testConfig.getTestVideo()), new File(testConfig.getOutputFolder()));
		videoProcessor.processMetadata();
	}
}
