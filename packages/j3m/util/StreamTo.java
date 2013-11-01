package util;

import java.io.InputStream;

public abstract class StreamTo implements Runnable {
	
	protected final static int BYTE_READ_SIZE = 8192;

	protected InputStream stream;
    
    protected byte[] getBytes(){
    	byte[] bytes = new byte[BYTE_READ_SIZE];
    	
    	return bytes;
    }

    public void setStream(InputStream is) {
    	stream = is;
    }
}
