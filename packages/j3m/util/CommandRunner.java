package util;

import java.io.BufferedWriter;
import java.io.OutputStreamWriter;
import java.util.Arrays;
public class CommandRunner {

	public int runCommand(String command, StreamTo processor) throws Exception {
        return runCommand(command,processor,null);
	}
	
	public int runCommand(String command, StreamTo processor, StringBuilder input) throws Exception {
		ProcessBuilder processBuilder = new ProcessBuilder(Arrays.asList(command.split(" ")));
		processBuilder.redirectErrorStream(true);
		Process p = processBuilder.start();
		processor.setStream(p.getInputStream());
		Thread processorThread = new Thread(processor, "output stream");
		processorThread.start();
		
		if(input != null){
			BufferedWriter out = new BufferedWriter(new OutputStreamWriter(p.getOutputStream()));
			out.write(input.toString());
			out.close();
		}
		p.waitFor(); 
		processorThread.join(100000);

        int exitValue = p.exitValue();
        return exitValue;
	}
	
}
