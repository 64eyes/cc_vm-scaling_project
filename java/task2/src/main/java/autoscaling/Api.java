package autoscaling;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.io.FileUtils;
import org.ini4j.Ini;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import utilities.HttpRequest;


/**
 * Server API Class.
 */
public final class Api {
    /**
     * Logger.
     */
    private static final Logger LOG = LoggerFactory.getLogger(Api.class);
    
    /**
     * Unused Constructor.
     */
    private Api() {
    }

    /**
     * Add an ELB.
     * @param loadGeneratorDNS LG DNS name
     * @param loadBalancerDNS ELB DNS name
     * @return return server response.
     */
    public static String initializeTest(final String loadGeneratorDNS,
                                        final String loadBalancerDNS) {
        String response = "";
        Boolean launchWebServiceSuccess = false;
        while (!launchWebServiceSuccess) {
            try {
                response = HttpRequest.sendGet(String.format(
                        "http://%s/autoscaling?dns=%s",
                        loadGeneratorDNS,
                        loadBalancerDNS));
                LOG.info(response);
                launchWebServiceSuccess = true;
            } catch (Exception e) {
                // ignore errors
            }
        }
        return response;
    }

    /**
     * Warm up an ELB.
     * @param loadGeneratorDNS LG DNS name
     * @param loadBalancerDNS ELB DNS Name
     * @return return response response
     */
    public static String initializeWarmup(final String loadGeneratorDNS,
                                          final String loadBalancerDNS) {
        String response = "";
        Boolean launchTestSuccess = false;
        while (!launchTestSuccess) {
            try {
                response = HttpRequest.sendGet(String.format(
                        "http://%s/warmup?dns=%s",
                        loadGeneratorDNS,
                        loadBalancerDNS));
                LOG.info(response);
                launchTestSuccess = true;
            } catch (Exception e) {
                // ignore errors
            }
        }
        return response;
    }

    /**
     * Get the latest version of the log.
     *
     * @param loadGeneratorDNS DNS Name of load generator
     * @param testId           TestID String
     * @return INI Object
     * @throws IOException on network failure
     */
    public static Ini getIniUpdate(final String loadGeneratorDNS,
                                   final String testId) throws IOException {
        String response = HttpRequest.sendGet(String.format(
                "http://%s/log?name=test.%s.log",
                loadGeneratorDNS,
                testId));
        File log = new File(testId + ".log");
        FileUtils.writeStringToFile(log, response, Charset.defaultCharset());
        Ini ini = new Ini(log);
        return ini;
    }

    /**
     * Get ID of test.
     *
     * @param response Response containing LoadGenerator output
     * @return TestID string
     */
    public static String getTestId(final String response) {
        Pattern pattern = Pattern.compile("test\\.([0-9]*)\\.log");
        Matcher matcher = pattern.matcher(response);
        if (matcher.find()) {
            return matcher.group(1);
        }
        return null;
    }
}
