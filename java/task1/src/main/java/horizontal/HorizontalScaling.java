package horizontal;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.Date;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.io.FileUtils;
import org.ini4j.Ini;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import utilities.Configuration;
import utilities.HttpRequest;

import software.amazon.awssdk.auth.credentials.AwsCredentialsProvider;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.services.ec2.Ec2Client;
import software.amazon.awssdk.services.ec2.model.Instance;
import software.amazon.awssdk.services.ec2.model.Vpc;
import software.amazon.awssdk.regions.Region;


/**
 * Class for Task1 Solution.
 */
public final class HorizontalScaling {
    /**
     * Project Tag value.
     */
    public static final String PROJECT_VALUE = "vm-scaling";

    /**
     * Configuration file.
     */
    private static final Configuration CONFIGURATION =
            new Configuration("horizontal-scaling-config.json");

    /**
     * Load Generator AMI.
     */
    private static final String LOAD_GENERATOR =
            CONFIGURATION.getString("load_generator_ami");
    
    /**
     * Web Service AMI.
     */
    private static final String WEB_SERVICE =
            CONFIGURATION.getString("web_service_ami");

    /**
     * Instance Type Name.
     */
    private static final String INSTANCE_TYPE =
            CONFIGURATION.getString("instance_type");

    /**
     * Web Service Security Group Name.
     */
    private static final String WEB_SERVICE_SECURITY_GROUP =
            "web-service-security-group";

    /**
     * Load Generator Security Group Name.
     */
    private static final String LG_SECURITY_GROUP =
            "lg-security-group";

    /**
     * HTTP Port.
     */
    private static final Integer HTTP_PORT = 80;

    /**
     * Launch Delay in milliseconds.
     */
    private static final long LAUNCH_DELAY = 100000;

    /**
     * RPS target to stop provisioning.
     */
    private static final float RPS_TARGET = 50;

    /**
     * Delay before retrying API call.
     */
    public static final int RETRY_DELAY_MILLIS = 100;

    /**
     * Logger.
     */
    private static Logger logger =
            LoggerFactory.getLogger(HorizontalScaling.class);

    /**
     * Private Constructor.
     */
    private HorizontalScaling() {
    }

    /**
     * Task1 main method.
     *
     * @param args No Args required
     * @throws Exception when something unpredictably goes wrong.
     */
    public static void main(final String[] args) throws Exception {
        // BIG PICTURE: Provision resources to achieve horizontal scalability
        //  - Create security groups for Load Generator and Web Service
        //  - Provision a Load Generator instance
        //  - Provision a Web Service instance
        //  - Register Web Service DNS with Load Generator
        //  - Add Web Service instances to Load Generator 
        //  - Terminate resources

        AwsCredentialsProvider credentialsProvider =
                DefaultCredentialsProvider.builder().build();

        // Create an Amazon EC2 Client
        Ec2Client ec2 = Ec2Client.builder()
                .region(Region.US_EAST_1)
                .credentialsProvider(credentialsProvider)
                .build();

        // Get the default VPC
        Vpc vpc = getDefaultVPC(ec2);

        // Create Security Groups in the default VPC
        String lgSecurityGroupId =
                getOrCreateHttpSecurityGroup(ec2, LG_SECURITY_GROUP, vpc.vpcId());
        String wsSecurityGroupId =
                getOrCreateHttpSecurityGroup(ec2, WEB_SERVICE_SECURITY_GROUP, vpc.vpcId());

        // TODO: Create Load Generator instance and obtain DNS
        // TODO: Tag instance using Tag Specification
        String loadGeneratorDNS = "";

        // TODO: Create first Web Service instance and obtain DNS
        // TODO: Tag instance using Tag Specification
        String webServiceDNS = "";

        //Initialize test
        String response = initializeTest(loadGeneratorDNS, webServiceDNS);

        //Get TestID
        String testId = getTestId(response);

        //Save launch time
        Date lastLaunchTime = new Date();

        //Monitor LOG file
        Ini ini = getIniUpdate(loadGeneratorDNS, testId);
        while (ini == null || !ini.containsKey("Test finished")) {
            ini = getIniUpdate(loadGeneratorDNS, testId);

            // TODO: Check last launch time and RPS
            // TODO: Add New Web Service Instance if Required
        }

    }

    /**
     * Get the latest RPS.
     *
     * @param ini INI file object
     * @return RPS Value
     */
    private static float getRPS(final Ini ini) {
        float rps = 0;
        for (String key : ini.keySet()) {
            if (key.startsWith("Current rps")) {
                rps = Float.parseFloat(key.split("=")[1]);
            }
        }
        return rps;
    }

    /**
     * Get the latest test log.
     *
     * @param loadGeneratorDNS DNS Name of load generator
     * @param testId           TestID String
     * @return INI Object
     * @throws IOException on network failure
     */
    private static Ini getIniUpdate(final String loadGeneratorDNS,
                                    final String testId)
            throws IOException {
        String response = HttpRequest.sendGet(String.format(
                "http://%s/log?name=test.%s.log",
                loadGeneratorDNS,
                testId));
        File log = new File(testId + ".log");
        FileUtils.writeStringToFile(log, response, Charset.defaultCharset());
        return new Ini(log);
    }

    /**
     * Get ID of test.
     *
     * @param response Response containing LoadGenerator output
     * @return TestID string
     */
    private static String getTestId(final String response) {
        Pattern pattern = Pattern.compile("test\\.([0-9]*)\\.log");
        Matcher matcher = pattern.matcher(response);
        if (matcher.find()) {
            return matcher.group(1);
        }
        return null;
    }

    /**
     * Initializes Load Generator Test.
     *
     * @param loadGeneratorDNS DNS Name of load generator
     * @param webServiceDNS    DNS Name of web service
     * @return response of initialization (contains test ID)
     */
    private static String initializeTest(final String loadGeneratorDNS,
                                         final String webServiceDNS) {
        String response = "";
        boolean launchWebServiceSuccess = false;
        while (!launchWebServiceSuccess) {
            try {
                response = HttpRequest.sendGet(String.format(
                        "http://%s/test/horizontal?dns=%s",
                        loadGeneratorDNS,
                        webServiceDNS));
                logger.info(response);
                launchWebServiceSuccess = true;
            } catch (Exception e) {
                // Retry until the instances are up and running
            }
        }
        return response;
    }

    /**
     * Add a Web Service vm to Load Generator.
     *
     * @param loadGeneratorDNS DNS Name of Load Generator
     * @param webServiceDNS    DNS Name of Web Service
     * @param testId           the test ID
     * @return String response
     */
    private static String addWebServiceInstance(final String loadGeneratorDNS,
                                                final String webServiceDNS,
                                                final String testId) {
        String response = "";
        boolean launchWebServiceSuccess = false;
        while (!launchWebServiceSuccess) {
            try {
                response = HttpRequest.sendGet(String.format(
                        "http://%s/test/horizontal/add?dns=%s",
                        loadGeneratorDNS,
                        webServiceDNS));
                logger.info(response);
                launchWebServiceSuccess = true;
            } catch (Exception e) {
                try {
                    Thread.sleep(RETRY_DELAY_MILLIS);
                    Ini ini = getIniUpdate(loadGeneratorDNS, testId);
                    if (ini.containsKey("Test finished")) {
                        launchWebServiceSuccess = true;
                        logger.info("New WS is not added because the test already completed");
                    }
                } catch (Exception e1) {
                    e1.printStackTrace();
                }
            }
        }
        return response;
    }

    /**
     * Get the default VPC.
     * <p>
     * With EC2-Classic, your instances run in a single, flat network that you share with other customers.
     * With Amazon VPC, your instances run in a virtual private cloud (VPC) that's logically isolated to your AWS account.
     * <p>
     * The EC2-Classic platform was introduced in the original release of Amazon EC2.
     * If you created your AWS account after 2013-12-04, it does not support EC2-Classic,
     * so you must launch your Amazon EC2 instances in a VPC.
     * <p>
     * By default, when you launch an instance, AWS launches it into your default VPC.
     * Alternatively, you can create a non-default VPC and specify it when you launch an instance.
     *
     * @param ec2 EC2 Client
     * @return the default VPC object
     */
    public static Vpc getDefaultVPC(final Ec2Client ec2) {
        //TODO: Remove the exception
        //TODO: Get the default VPC
        throw new UnsupportedOperationException();
    }

    /**
     * Get or create a security group and allow all HTTP inbound traffic.
     *
     * @param ec2               EC2 Client
     * @param securityGroupName the name of the security group
     * @param vpcId             the ID of the VPC
     * @return ID of security group
     */
    public static String getOrCreateHttpSecurityGroup(final Ec2Client ec2,
                                                      final String securityGroupName,
                                                      final String vpcId) {
        //TODO: Remove the exception
        //TODO: Get or create Security Group
        //TODO: Allow all HTTP inbound traffic for the security group
        throw new UnsupportedOperationException();
    }

    /**
     * Get instance object by ID.
     *
     * @param ec2        EC2 client instance
     * @param instanceId instance ID
     * @return Instance Object
     */
    public static Instance getInstance(final Ec2Client ec2,
                                       final String instanceId) {
        //TODO: Remove the exception
        //TODO: Get an Ec2 instance
        throw new UnsupportedOperationException();
    }
}
