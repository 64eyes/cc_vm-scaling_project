package autoscaling;

import software.amazon.awssdk.services.ec2.Ec2Client;
import software.amazon.awssdk.services.ec2.model.Instance;
import software.amazon.awssdk.services.ec2.model.Tag;
import software.amazon.awssdk.services.ec2.model.TagSpecification;
import software.amazon.awssdk.services.ec2.model.Vpc;

import java.util.Arrays;
import java.util.List;

import static autoscaling.AutoScale.PROJECT_VALUE;
import static autoscaling.AutoScale.TYPE_VALUE;
import static autoscaling.AutoScale.ROLE_VALUE;
import static autoscaling.AutoScale.EOL_VALUE;;


/**
 * Class to manage EC2 resources.
 */
public final class Ec2 {
    /**
     * EC2 Tags List
     */
    private static final List<Tag> EC2_TAGS_LIST = Arrays.asList(
            Tag.builder().key("Project").value(PROJECT_VALUE).build(),
            Tag.builder().key("Type").value(TYPE_VALUE).build(),
            Tag.builder().key("Role").value(ROLE_VALUE).build(),
            Tag.builder().key("EOL").value(EOL_VALUE).build());

    /**
     * Unused default constructor.
     */
    private Ec2() {
    }

    /**
     * Launch an Ec2 Instance.
     *
     * @param ec2                EC2Client
     * @param tagSpecification   TagsSpecified to create instance
     * @param amiId              amiId
     * @param instanceType       Type of instance
     * @param securityGroupId    Security Group
     * @param detailedMonitoring With Detailed Monitoring Enabled
     * @return Instance object
     */
    public static Instance launchInstance(final Ec2Client ec2,
                                          final TagSpecification tagSpecification,
                                          final String amiId,
                                          final String instanceType,
                                          final String securityGroupId,
                                          final Boolean detailedMonitoring) throws InterruptedException {
        // TODO: Launch a new Instance
        throw new UnsupportedOperationException("Not yet implemented.");
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
        // TODO: Get or Create a Security Group if necessary
        // TODO: Authorize ingress HTTP traffic
        throw new UnsupportedOperationException("Not yet implemented.");
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
        // TODO: Return the default VPC
        throw new UnsupportedOperationException("Not yet implemented.");
    }

    /**
     * Create launch template.
     * 
     * @param ec2 Ec2 Client
     */
    static void createLaunchTemplate(final Ec2Client ec2) {
        // TODO: Create a Launch Template
        throw new UnsupportedOperationException("Not yet implemented.");
    }

    /**
     * Terminate an Instance.
     *
     * @param ec2        Ec2 client
     * @param instanceId Instance Id to terminate
     */
    public static void terminateInstance(final Ec2Client ec2, final String instanceId) {
        // TODO: Terminate an Instance
        throw new UnsupportedOperationException("Not yet implemented.");
    }

    /**
     * Delete a Security group.
     *
     * @param ec2              ec2 client
     * @param elbSecurityGroup security group name
     */
    public static void deleteSecurityGroup(final Ec2Client ec2,
                                           final String elbSecurityGroup) {
        // TODO: Delete a Security Group
        throw new UnsupportedOperationException("Not yet implemented.");
    }

    /**
     * Delete launch template.
     *
     * @param ec2 Ec2 Client instance
     */
    public static void deleteLaunchTemplate(final Ec2Client ec2) {
        // TODO: Delete a Launch Template
        throw new UnsupportedOperationException("Not yet implemented.");
    }
}
