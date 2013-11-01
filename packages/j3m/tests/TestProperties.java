package tests;

import java.util.Properties;


public class TestProperties {

	private Properties properties;
	private static TestProperties instance;
	
	private void setProperties (Properties properties){
		this.properties = properties;
	}
	
	public String getOutputFolder() {
		return properties.getProperty("output_folder");
	}
	public String getTestImage() {
		return properties.getProperty("test_image");
	}
	public String getTestVideo() {
		return properties.getProperty("test_video");
	}
	public String getTestJ3M() {
		return properties.getProperty("test_j3m");
	}
	
	public String getTesZippedtJ3M() {
		return properties.getProperty("test_zipped_j3m");
	}
	
	public String getDirtyJ3M() {
		return properties.getProperty("test_dirty_j3m");
	}
	
	public String getSignedJ3M() {
		return properties.getProperty("test_signed_j3m");
	}
	
	public String getEncryptedJ3M() {
		return properties.getProperty("test_encoded_j3m");
	}
	public String getAudioJ3M() {
		return properties.getProperty("test_audio_j3m");
	}
	
	public String getImageToHash() {
		return properties.getProperty("test_image_to_hash");
	}
	public String getImageHash() {
		return properties.getProperty("test_image_hash");
	}
	public String getImageHashJ3M() {
		return properties.getProperty("test_image_hash_j3m");
	}
	
	public static TestProperties getInstance() {
		   if(instance == null) {
			  
			  instance = new TestProperties(); 
		
			  Properties _properties = new Properties();
		   	  try {
				_properties.load(Thread.currentThread().getContextClassLoader().getResourceAsStream("test.properties"));
				} catch (Exception e) {
					throw new RuntimeException("Could not load properties file", e);
				}
		   	  instance.setProperties(_properties);
		   }
		   return instance;
		}
}
