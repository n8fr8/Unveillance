package framework;

import java.util.Arrays;
import java.util.List;
import java.util.Properties;


public class FrameworkProperties {


	private Properties properties;
	private static FrameworkProperties instance;
	
	private void setProperties (Properties properties){
		this.properties = properties;
	}
	
	public boolean getLenient() {
		return Boolean.valueOf(properties.getProperty("framework_lenient"));
	}
	public boolean getVerbose() {
		return Boolean.valueOf(properties.getProperty("framework_verbose"));
	}
	public void setLenient(boolean setting) {
		properties.setProperty("framework_lenient",String.valueOf(setting));
	}
	public void setVerbose(boolean setting) {
		properties.setProperty("framework_verbose",String.valueOf(setting));
	}
	public boolean getDebug() {
		return Boolean.valueOf(properties.getProperty("framework_debug"));
	}
	public void setDebug(boolean setting) {
		properties.setProperty("framework_debug",String.valueOf(setting));
	}
	public List<String> getKeywordContainers() {
		return Arrays.asList(properties.getProperty("keyword_container_elements").split(","));
	}
	public List<String> getKeywordExclussions() {
		return Arrays.asList(properties.getProperty("keywords_excluded_words").split(","));
	}
	public String getSignatureContainer() {
		return properties.getProperty("gpg_signature");
	}
	public String getJ3mContainer() {
		return properties.getProperty("j3m_body");
	}
	public String getAudioContainer() {
		return properties.getProperty("audio_file");
	}
	public String getAudioRawFormat() {
		return properties.getProperty("audio_raw_format");
	}
	public String getAudioTargetFormat() {
		return properties.getProperty("audio_target_format");
	}
	
	public String getGpgVerifySignature() {
		return properties.getProperty("gpg_verify_signature");
	}
	public String getGpgSignatureOK() {
		return properties.getProperty("gpg_signature_verified");
	}
	public String getGpgDecrypt() {
		return properties.getProperty("gpg_decrypt");
	}
	public String getGpgPassword() {
		return properties.getProperty("gpg_password_file");
	}
	
	public String getJ3MGetMetadata() {
		return properties.getProperty("j3m_get_metadata");
	}
	public List<String> getJ3MIgnoreLines() {
		return Arrays.asList(properties.getProperty("j3m_output_ignore_lines").split(";"));
	}
	
	public String getFfmpegVersion() {
		return properties.getProperty("ffmpeg_version");
	}
	public String getFfmpegGetAttachment() {
		return properties.getProperty("ffmpeg_get_attachement");
	}
	public List<String> getVideoInputTypes() {
		return Arrays.asList(properties.getProperty("video_input_types").split(","));
	}
	public List<String> getImageInputTypes() {
		return Arrays.asList(properties.getProperty("image_input_types").split(","));
	}


	public String getVideoInputTypesString() {
		return properties.getProperty("video_input_types");
	}
	public String getImageInputTypesString() {
		return properties.getProperty("image_input_types");
	}
	public String getImageMetadataFileExt() {
		return properties.getProperty("image_metadata_file_ext");
	}
	public String getImageKeywordsFileExt() {
		return properties.getProperty("image_keywords_file_ext");
	}
	public String getVideoMetadataFileExt() {
		return properties.getProperty("video_metadata_file_ext");
	}
	public String getVideoStillFileExt() {
		return properties.getProperty("video_still_file_ext");
	}
	public String getVideoConvertedFormat() {
		return properties.getProperty("video_converted_format");
	}
	public String getThumbFileExt() {
		return properties.getProperty("image_thumb_file_ext");
	}
	public int getThumbHeight() {
		return Integer.parseInt(properties.getProperty("image_thumb_height"));
	}
	public int getThumbWidth() {
		return Integer.parseInt(properties.getProperty("image_thumb_width"));
	}
	public String getImageSmallHeight() {
		return properties.getProperty("image_small_height");
	}
	public String getImageSmallWidth() {
		return properties.getProperty("image_small_width");
	}
	public String getImageMedHeight() {
		return properties.getProperty("image_med_height");
	}
	public String getImageMedWidth() {
		return properties.getProperty("image_med_width");
	}
	public String getImageLargeHeight() {
		return properties.getProperty("image_large_height");
	}
	public String getImageLargeWidth() {
		return properties.getProperty("image_large_width");
	}
	public String getVideoSmallHeight() {
		return properties.getProperty("video_small_height");
	}
	public String getVideoSmallWidth() {
		return properties.getProperty("video_small_width");
	}
	public String getVideoMedHeight() {
		return properties.getProperty("video_med_height");
	}
	public String getVideoMedWidth() {
		return properties.getProperty("video_med_width");
	}
	public String getVideoLargeHeight() {
		return properties.getProperty("video_large_height");
	}
	public String getVideoLargeWidth() {
		return properties.getProperty("video_large_width");
	}
	public String getffmpegChangeFormat() {
		return properties.getProperty("ffmpeg_change_format");
	}
	public String getffmpegChangeResolution() {
		return properties.getProperty("ffmpeg_change_resolution");
	}
	public String getffmpegCreateStill() {
		return properties.getProperty("ffmpeg_create_still");
	}
	public String getffmpeg2Theora() {
		return properties.getProperty("ffmpeg_theora");
	}
	public String getffmpegRGB() {
		return properties.getProperty("ffmpeg_frame_rgb");
	}
	public String getffmpegVideoRgbMd5() {
		return properties.getProperty("ffmpeg_video_rgb_md5");
	}
	public String getffmpegAudioMd5() {
		return properties.getProperty("ffmpeg_audio_md5");
	}
	public String getffmpegAudioConvert() {
		return properties.getProperty("ffmpeg_audio_convert");
	}
	
	
	public String getSalt(){
		return properties.getProperty("salt");
	}
	
	public String getHashMismatchWarningVideo(){
		return properties.getProperty("video_hash_mismatch_warning");
	}public String getHashMismatchWarning(){
		return properties.getProperty("audio_hash_mismatch_warning");
	}public String getHashMismatchWArningImage(){
		return properties.getProperty("image_hash_mismatch_warning");
	}

	public String getVideoHashPath(){
		return properties.getProperty("video_hash_path");
	}public String getAudioHashPath(){
		return properties.getProperty("audio_hash_path");
	}public String getImageHashPath(){
		return properties.getProperty("image_hash_path");
	}
	
	protected FrameworkProperties() {
		super();
		// TODO Auto-generated constructor stub
	}
	
	
	public static FrameworkProperties getInstance() {
	   if(instance == null) {
		  
		  instance = new FrameworkProperties(); 
	
		  Properties _properties = new Properties();
	   	  try {
			_properties.load(Thread.currentThread().getContextClassLoader().getResourceAsStream("conf.properties"));
			} catch (Exception e) {
				throw new RuntimeException("Could not load properties file", e);
			}
	   	  instance.setProperties(_properties);
	   }
	   return instance;
	}
	
	/* Util methods that only apply to the properties of the framework
	 * 
	 */
	public static void processError(String message, Throwable cause )throws Exception{
		if (FrameworkProperties.getInstance().getVerbose()) {
			System.err.println(message + "\n cause: " );
			cause.printStackTrace(System.err);
		}
		if (!FrameworkProperties.getInstance().getLenient()){
			throw new Exception(message, cause);
		}
	}
	public static void processMessage(String message) {
		if (FrameworkProperties.getInstance().getVerbose()) {
			System.out.println(message);
		}
	}
	
	/**
	 * 
	 * @param expression has to be in the format <multiplier>;<addition>
	 * @param originalValue
	 * @return
	 */
	public static int evaluateDemension(String expression, int originalValue){
		String[] vals = expression.split(";");
		Integer i = new Integer(originalValue);
		Double temp = new Double(i.doubleValue());
		//was that dumb? it felt dumb
		if (vals[0] != null) {
			temp = originalValue * Double.parseDouble(vals[0]);
		}
		if (vals[1] != null) {
			temp +=  Double.parseDouble(vals[1]);
		}
		return temp.intValue();
	}
	
}
