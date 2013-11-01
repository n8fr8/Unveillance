package tests;

import java.io.File;

import org.apache.commons.io.FileUtils;
import org.junit.Assert;
import org.junit.Test;

import framework.FrameworkProperties;
import framework.J3mMetadataProcessor;

public class J3mMetadataProcessorTests {
	
	FrameworkProperties config = FrameworkProperties.getInstance();
	TestProperties testConfig = TestProperties.getInstance();

	
	@Test
	public void parseKeyWordsTest() throws Exception {
		File metadata = new File(testConfig.getTestJ3M());
		File outFile = new File(testConfig.getOutputFolder()+ "testKeywords.json");
		long timestamp = System.currentTimeMillis();
		J3mMetadataProcessor metadataProcessor = new J3mMetadataProcessor(metadata,new File(testConfig.getOutputFolder()));
		metadataProcessor.parseKeyWords();
		if (!outFile.exists()){
		    Assert.fail("Extracted key words file " + outFile.getPath() + " does not exist");
		}
		Assert.assertTrue("keyword file timestamp doesnt reflect operation", timestamp < outFile.lastModified());

	}

	
	@Test
	public void toJSONTest ()throws Exception {
		File metadata = new File(testConfig.getEncryptedJ3M());
		long timestamp = System.currentTimeMillis();
		File testOut = File.createTempFile(String.valueOf(System.currentTimeMillis()), ".unb64");
		J3mMetadataProcessor metadataProcessor = new J3mMetadataProcessor(metadata,new File(testConfig.getOutputFolder()));
		metadataProcessor.toJSON();
		if (!testOut.exists()){
		    Assert.fail("Decoded file " + testOut.getPath() + " does not exist");
		}
		Assert.assertTrue("decoded file timestamp doesnt reflect operation", timestamp < testOut.lastModified());

	}
	@Test 
	public void extractAudioTest() throws Exception{
		File audioJ3M = new File(testConfig.getAudioJ3M());
		File temp = new File(audioJ3M.getParent(), audioJ3M.getName() + ".temp");
		FileUtils.copyFile(audioJ3M,temp);
		long timestamp = System.currentTimeMillis();
		J3mMetadataProcessor metadataProcessor = new J3mMetadataProcessor(temp,new File(testConfig.getOutputFolder()));
		config.setDebug(true);
		File testOut = metadataProcessor.extractAudio();
		if (!testOut.exists()){
		    Assert.fail("Decoded file " + testOut.getPath() + " does not exist");
		}
		Assert.assertTrue("decoded file timestamp doesnt reflect operation", timestamp < testOut.lastModified());
		timestamp = System.currentTimeMillis();
		try {
			testOut = metadataProcessor.extractAudio();
			Assert.fail("BLOB replacement failed");
		}catch (Exception e) {
			Assert.assertTrue("JSON file erronoously updated althogh ausio BLOB should have been removed", timestamp < testOut.lastModified());
		}
	}
}
