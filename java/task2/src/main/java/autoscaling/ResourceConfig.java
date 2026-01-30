package autoscaling;

/**
 * Resource Configuration Class.
 */
public class ResourceConfig {

    /**
     * Load Generator ID.
     */
    private String loadGeneratorID;

    /**
     * Target Group ARN.
     */
    private String targetGroupArn;

    /**
     * Load Generator DNS.
     */
    private String loadGeneratorDns;

    /**
     * Load Balancer Arn.
     */
    private String loadBalancerArn;

    /**
     * Load Balancer DNS.
     */
    private String loadBalancerDns;

    public String getLoadGeneratorID() {
        return loadGeneratorID;
    }

    public void setLoadGeneratorID(String loadGeneratorID) {
        this.loadGeneratorID = loadGeneratorID;
    }

    public String getTargetGroupArn() {
        return this.targetGroupArn;
    }

    public void setTargetGroupArn(String targetGroupArn) {
        this.targetGroupArn = targetGroupArn;
    }


    public String getLoadGeneratorDns() {
        return loadGeneratorDns;
    }

    public void setLoadGeneratorDns(String loadGeneratorDns) {
        this.loadGeneratorDns = loadGeneratorDns;
    }

    public String getLoadBalancerArn() {
        return loadBalancerArn;
    }

    public void setLoadBalancerArn(String loadBalancerArn) {
        this.loadBalancerArn = loadBalancerArn;
    }

    public String getLoadBalancerDns() {
        return loadBalancerDns;
    }

    public void setLoadBalancerDns(String loadBalancerDns) {
        this.loadBalancerDns = loadBalancerDns;
    }
}
