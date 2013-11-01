package util;

public class StreamToStdOut extends StreamTo {
	

	public void run() {
        try {
        	int c;
            while ((c = stream.read()) != -1) {
                System.out.write(c);
            }
        } catch (Throwable t) {
            t.printStackTrace();
        }
    }

}
