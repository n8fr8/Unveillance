package tests;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Arrays;

import org.junit.Test;
import org.junit.Assert;

import framework.FrameworkProperties;

public class PropertiesTest {
	
/**
 * makes sure all the necessary resource are provided in the conf file and are accsessoble
 * @throws Exception
 */
	@Test
	public void initTest() throws Exception {
		FrameworkProperties config;
		try {
			config = FrameworkProperties.getInstance();
		} catch (Exception e) {
			Assert.fail("could not load properties file");
			throw e;
		}
		//file formats
		try {				
			Assert.assertTrue(config.getImageInputTypes().contains("jpg"));
		} catch (Exception e) {
			Assert.fail("could not process image formats");
		}
		try {				
			Assert.assertTrue(config.getVideoInputTypes().contains("mkv"));
		} catch (Exception e) {
			Assert.fail("could not process video formats");
		}
		//keywords containers and excluded words
		try {				
			Assert.assertTrue(config.getKeywordContainers().size()>0);
		} catch (Exception e) {
			Assert.fail("could not process keywords containers");
		}
		try {				
			Assert.assertTrue(config.getKeywordExclussions().size()>0);
		} catch (Exception e) {
			Assert.fail("could not process keyword exclussions");
		}
		try {				
			Assert.assertTrue(config.getJ3MIgnoreLines().size()>0);
		} catch (Exception e) {
			Assert.fail("could not process j3m output ignore lines");
		}
		Assert.assertNotNull("No j3m metadata a command", config.getJ3MGetMetadata());
		
		Assert.assertNotNull("No j3m container", config.getJ3mContainer());
		Assert.assertNotNull("No signature container", config.getSignatureContainer());
		Assert.assertNotNull("No audio container", config.getAudioContainer());
		
		Assert.assertNotNull("No gpg_verify_signature", config.getGpgVerifySignature());
		Assert.assertNotNull("No gpg_signature_verified", config.getGpgSignatureOK());
		Assert.assertNotNull("No gpg_decrypt", config.getGpgDecrypt());
		Assert.assertNotNull("No gpg_password_file", config.getGpgPassword());
		
		Assert.assertNotNull("No image metadata file type", config.getImageMetadataFileExt());
		Assert.assertNotNull("No image keywords file type", config.getImageKeywordsFileExt());
		Assert.assertNotNull("No video metadata file type", config.getVideoMetadataFileExt());
		Assert.assertNotNull("No video still file type", config.getVideoStillFileExt());
		Assert.assertNotNull("No video conversion file type", config.getVideoConvertedFormat());
		
		Assert.assertNotNull("No audio raw format", config.getAudioRawFormat());
		Assert.assertNotNull("No audio target format", config.getAudioTargetFormat());
	
		
		Assert.assertNotNull("No ffmpeg@theora command", config.getffmpeg2Theora());
		Assert.assertNotNull("No ffmpeg_frame_rgb command", config.getffmpegRGB());
		Assert.assertNotNull("No ffmpeg_video_rgb_md5 command", config.getffmpegVideoRgbMd5());
		Assert.assertNotNull("No ffmpeg_audio_md5 command", config.getffmpegAudioMd5());
		Assert.assertNotNull("No ffmpeg_audio_convert command", config.getffmpegAudioConvert());
		
		
		Assert.assertNotNull("No salt command", config.getSalt());
		Assert.assertNotNull("No video_hash_mismatch_warning command", config.getHashMismatchWarningVideo());
		Assert.assertNotNull("No audio_hash_mismatch_warning command", config.getHashMismatchWarning());
		Assert.assertNotNull("No image_hash_mismatch_warning command", config.getHashMismatchWArningImage());
		Assert.assertNotNull("No video_hash_path command", config.getVideoHashPath());
		Assert.assertNotNull("No audio_hash_path command", config.getAudioHashPath());
		Assert.assertNotNull("No image_hash_path command", config.getImageHashPath());
		
		Assert.assertNotNull("No thumb file type", config.getThumbFileExt());
		Assert.assertTrue("No thumb file width", 0 < config.getThumbWidth());
		Assert.assertTrue("No thumb file height", 0 < config.getThumbHeight());
		
		Assert.assertNotNull("No small image width",  config.getImageSmallWidth());
		Assert.assertNotNull("No small image height", config.getImageSmallHeight());
		Assert.assertNotNull("No med image width",config.getImageMedWidth());
		Assert.assertNotNull("No med image height", config.getImageMedHeight());
		Assert.assertNotNull("No large image width", config.getImageLargeWidth());
		Assert.assertNotNull("No large image height", config.getImageLargeHeight());
		
		Assert.assertNotNull("No small video width", config.getVideoSmallWidth());
		Assert.assertNotNull("No small video height", config.getVideoSmallHeight());
		Assert.assertNotNull("No med video width", config.getVideoMedWidth());
		Assert.assertNotNull("No med video height", config.getVideoMedHeight());
		Assert.assertNotNull("No large video width", config.getVideoLargeWidth());
		Assert.assertNotNull("No large video height", config.getVideoLargeHeight());
		
	
		//config.setLenient(true);
		//config.setVerbose(true);
		Assert.assertTrue(config.getVerbose());
		Assert.assertTrue(config.getLenient());
	
		
		//check ffmpeg is working
		ProcessBuilder processBuilder = new ProcessBuilder(Arrays.asList(config.getFfmpegVersion().split(" ")));
		processBuilder.redirectErrorStream(true);
		Process p = processBuilder.start(); 
		p.waitFor(); 
		BufferedReader reader=new BufferedReader(new InputStreamReader(p.getInputStream())); 
		String line=reader.readLine(); 
		if (!line.contains("ffmpeg version")) 
		{ 
			Assert.fail("could not run ffmpeg from command line");
		} 

	}

}
