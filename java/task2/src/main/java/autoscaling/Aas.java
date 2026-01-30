package autoscaling;

import java.util.Arrays;
import java.util.List;

import software.amazon.awssdk.services.autoscaling.AutoScalingClient;
import software.amazon.awssdk.services.autoscaling.model.Tag;
import software.amazon.awssdk.services.cloudwatch.CloudWatchClient;

import static autoscaling.AutoScale.EOL_VALUE;
import static autoscaling.AutoScale.PROJECT_VALUE;
import static autoscaling.AutoScale.ROLE_VALUE;
import static autoscaling.AutoScale.TYPE_VALUE;
import static autoscaling.AutoScale.configuration;


/**
 * Amazon AutoScaling resource class.
 */
public final class Aas {
    /**
     * Max size of ASG.
     */
    private static final Integer MAX_SIZE_ASG =
            configuration.getInt("asg_max_size");
    
    /**
     * Min size of ASG.
     */
    private static final Integer MIN_SIZE_ASG =
            configuration.getInt("asg_min_size");

    /**
     * Health Check grace period.
     */
    private static final Integer HEALTH_CHECK_GRACE_PERIOD =
            configuration.getInt("health_check_grace_period");
    
    /**
     * Cool down period Scale In.
     */
    private static final Integer COOLDOWN_PERIOD_SCALEIN =
            configuration.getInt("cool_down_period_scale_in");

    /**
     * Cool down period Scale Out.
     */
    private static final Integer COOLDOWN_PERIOD_SCALEOUT =
            configuration.getInt("cool_down_period_scale_out");

    /**
     * Number of instances to scale out by.
     */
    private static final Integer SCALING_OUT_ADJUSTMENT =
            configuration.getInt("scale_out_adjustment");
    
    /**
     * Number of instances to scale in by.
     */
    private static final Integer SCALING_IN_ADJUSTMENT =
            configuration.getInt("scale_in_adjustment");

    /**
     * ASG Cool down period in seconds.
     */
    private static final Integer COOLDOWN_PERIOD_ASG =
            configuration.getInt("asg_default_cool_down_period");

    /**
     * AAS Tags List.
     */
    private static final List<Tag> AAS_TAGS_LIST = Arrays.asList(
            Tag.builder().key("Project").value(PROJECT_VALUE).build(),
            Tag.builder().key("Type").value(TYPE_VALUE).build(),
            Tag.builder().key("Role").value(ROLE_VALUE).build(),
            Tag.builder().key("EOL").value(EOL_VALUE).build());

    /**
     * Unused constructor.
     */
    private Aas() {
    }

    /**
     * Create auto scaling group.
     * Create and attach Cloud Watch Policies.
     *
     * @param aas            AAS Client
     * @param cloudWatch     CloudWatch client
     * @param targetGroupArn target group arn
     */
    public static void createAutoScalingGroup(final AutoScalingClient aas,
                                              final CloudWatchClient cloudWatch,
                                              final String targetGroupArn) {
        // TODO: Create an Auto Scaling Group with a launch template
        // TODO: Create and attach CloudWatch policies to the Auto Scaling Group
        throw new UnsupportedOperationException("Not yet implemented.");
    }

    /**
     * Terminate auto scaling group.
     *
     * @param aas AAS client
     */
    public static void terminateAutoScalingGroup(final AutoScalingClient aas) {
        // TODO: Delete the Auto Scaling Group
        throw new UnsupportedOperationException("Not yet implemented.");
    }
}
