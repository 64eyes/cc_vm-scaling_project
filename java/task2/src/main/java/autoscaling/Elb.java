package autoscaling;

import java.util.Arrays;
import java.util.List;

import software.amazon.awssdk.services.ec2.Ec2Client;
import software.amazon.awssdk.services.elasticloadbalancingv2.ElasticLoadBalancingV2Client;
import software.amazon.awssdk.services.elasticloadbalancingv2.model.LoadBalancer;
import software.amazon.awssdk.services.elasticloadbalancingv2.model.Tag;
import software.amazon.awssdk.services.elasticloadbalancingv2.model.TargetGroup;

import static autoscaling.AutoScale.EOL_VALUE;
import static autoscaling.AutoScale.PROJECT_VALUE;
import static autoscaling.AutoScale.ROLE_VALUE;
import static autoscaling.AutoScale.TYPE_VALUE;


/**
 * ELB resources class.
 */
public final class Elb {
    /**
     * ELB Tags.
     */
    public static final List<Tag> ELB_TAGS_LIST = Arrays.asList(
            Tag.builder().key("Project").value(PROJECT_VALUE).build(),
            Tag.builder().key("Type").value(TYPE_VALUE).build(),
            Tag.builder().key("Role").value(ROLE_VALUE).build(),
            Tag.builder().key("EOL").value(EOL_VALUE).build());

    /**
     * Unused default constructor.
     */
    private Elb() {
    }

    /**
     * Create a target group.
     *
     * @param elb elb client
     * @param ec2 ec2 client
     * @return target group instance
     */
    public static TargetGroup createTargetGroup(
            final ElasticLoadBalancingV2Client elb,
            final Ec2Client ec2) {
        // TODO: Create a Target Group
        throw new UnsupportedOperationException("Not yet implemented.");
    }

    /**
     * create a load balancer.
     *
     * @param elb             ELB client
     * @param ec2             EC2 client
     * @param securityGroupId Security group ID
     * @param targetGroupArn  target group ARN
     * @return Load balancer instance
     */
    public static LoadBalancer createLoadBalancer(
            final ElasticLoadBalancingV2Client elb,
            final Ec2Client ec2,
            final String securityGroupId,
            final String targetGroupArn) {
        // TODO: Create a Load Balancer in the us-east-1 region
        // TODO: Create and attach listener to the Load Balancer
        throw new UnsupportedOperationException("Not yet implemented.");
    }

    /**
     * Delete a load balancer.
     *
     * @param elb             LoadBalancing client
     * @param loadBalancerArn load balancer ARN
     */
    public static void deleteLoadBalancer(final ElasticLoadBalancingV2Client elb,
                                          final String loadBalancerArn) {
        // TODO: Delete Load Balancer
        throw new UnsupportedOperationException("Not yet implemented.");
    }

    /**
     * Delete Target Group.
     *
     * @param elb            ELB Client
     * @param targetGroupArn target Group ARN
     */
    public static void deleteTargetGroup(final ElasticLoadBalancingV2Client elb,
                                         final String targetGroupArn) {
        // TODO: Delete Target Group
        throw new UnsupportedOperationException("Not yet implemented.");
    }
}
