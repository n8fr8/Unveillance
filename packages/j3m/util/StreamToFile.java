package util;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;

public class StreamToFile extends StreamTo {
    private File outFile = null;

	public StreamToFile(File outFile) {
		super();
		this.outFile = outFile;
	}
    
    public void run() {
    	try {
			FileWriter writer = new FileWriter(outFile);
			BufferedWriter out = new BufferedWriter(writer);
			int c;
			try {
				while ((c = stream.read()) != -1) {
				    out.write(c);
				}
			}finally {
				out.close();
			}
		}catch (Throwable t) {
       	  	t.printStackTrace();
		}
    }
}
