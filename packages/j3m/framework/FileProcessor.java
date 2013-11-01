package framework;

import java.io.File;
import util.Util;

public abstract class FileProcessor {

	private File sourceFile; 
	private File outputFolder;
	private String sourceFileName;
	
	public FileProcessor(File sourceFile, File outputFolder) {
		super();
		this.sourceFile = sourceFile;
		this.outputFolder = outputFolder;
		sourceFileName = Util.getBaseFileName(sourceFile);
	}
	
	protected FileProcessor() {
		super();
	}
	
	public void setSourceFile(File sourceFile){
		this.sourceFile = sourceFile;
	}
	public void setOutputFolder(File outputFolder){
		this.outputFolder = outputFolder;
	}

	public File getSourceFile() {
		return sourceFile;
	}

	public File getOutputFolder() {
		return outputFolder;
	}
	
	public String getSourceFileName() {
		return sourceFileName;
	}
}
