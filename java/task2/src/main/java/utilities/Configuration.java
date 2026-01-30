package utilities;

import org.apache.commons.io.FileUtils;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;

public class Configuration {
    private JSONObject config;

    public Configuration(String fileName) {
        File configFile = new File(this.getClass().getClassLoader().getResource(fileName).getFile());
        try {
            config = new JSONObject(FileUtils.readFileToString(configFile,
                    Charset.defaultCharset()));
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public String getString(String key) {
        return config.getString(key);
    }

    public Integer getInt(String key) {
        return config.getInt(key);
    }

    public Double getDouble(String key) {
        return config.getDouble(key);
    }
}
