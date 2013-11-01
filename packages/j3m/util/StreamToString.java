package util;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Scanner;

public class StreamToString extends StreamTo {
    private String result;
    private String pattern;
    
    public StreamToString(String pattern) {
		super();
		this.pattern = pattern;
	}
    
    //TODO this is kinda slow, maybe take out the scanner and do a simpler search
    public void run() {
    	if (pattern != null) {
        	Scanner scanner = new Scanner(stream).useDelimiter(pattern);
        	scanner.findWithinHorizon(pattern, 0);
        	try {
				result = scanner.match().group(2);
			} catch (IllegalStateException e) {
				//no match found
				result = null;
			}
    	}else {
    		BufferedReader reader = new BufferedReader(new InputStreamReader(stream));
    		try {
				String line = reader.readLine();
				while (line != null) {
					result += line;
					line = reader.readLine();
				}
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
    	}

    }
    
    public String getResult()  {
    	return result;
    }
}
