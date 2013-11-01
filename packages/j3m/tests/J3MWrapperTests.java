package tests;

import j3m.J3MWrapper;

import java.io.File;

import org.junit.Assert;
import org.junit.Test;

import util.Util;

import framework.FrameworkProperties;

public class J3MWrapperTests {
	FrameworkProperties config = FrameworkProperties.getInstance();
	TestProperties testConfig = TestProperties.getInstance();

	@Test
	public void extractMetaDataTest () throws Exception{
		J3MWrapper wrapper = new J3MWrapper();
		
		File inFile = new File(testConfig.getTestImage());
		String output = testConfig.getOutputFolder() + Util.getBaseFileName(inFile) + "." + config.getImageMetadataFileExt();
		long timestamp = System.currentTimeMillis();
		File outputFile = new File(output);
		wrapper.extractMetaData(inFile, outputFile);
		if (!outputFile.exists()){
		    Assert.fail("Extracted metadata file " + outputFile.getPath() + " does not exist");
		}
		Assert.assertTrue("Metadata file timestamp doesnt reflect operation", timestamp < outputFile.lastModified());
	}
	
	@Test
	public void testCleanFile() throws Exception {
		File inFile = new File(testConfig.getDirtyJ3M());
		J3MWrapper wrapper = new J3MWrapper();
		long timestamp = System.currentTimeMillis();
		wrapper.cleanFile(inFile);
		Assert.assertTrue("Output file not created", inFile.exists());
		Assert.assertTrue("Output file timestamp doesnt reflect operation", timestamp < inFile.lastModified());

	}
}
