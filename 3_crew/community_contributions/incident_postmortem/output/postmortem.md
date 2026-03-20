# Postmortem: checkout-api 

## Metadata
- **Severity:** SEV-2
- **Report date:** 2026-03-20
- **Service:** checkout-api

## Summary
On March 18, 2025, the checkout-api experienced an incident due to a misconfiguration during deployment, resulting in a spike in error rates and failed transactions. The root cause was identified as the PAYMENTS_RETRY_MAX config flag being erroneously set to 0. Through timely detection and effective response strategies, the issue was resolved, but improvements are necessary to prevent future occurrences.

## Timeline
- **2025-03-18 09:12** — Monitoring system detected that the checkout-api error rate exceeded 5% in the us-east-1 region.
- **2025-03-18 09:18** — On-call team initiated action by restarting two unhealthy pods. Error rates briefly decreased but then rose again.
- **2025-03-18 09:35** — Investigation revealed that a recent deployment had a configuration error; the config flag PAYMENTS_RETRY_MAX was set to 0 in production by mistake.
- **2025-03-18 09:50** — The system was rolled back to the previous release. Normalization of the error rate was observed within minutes.
- **2025-03-18 10:05** — Incident was officially closed after confirming the error rate returned to normal. 

## Impact
- An estimated total of **12,000 failed checkout transactions** occurred over a duration of approximately **43 minutes** in the us-east-1 region.
- There was **no data loss** reported during this time frame, and SLAs for transaction processing were unfulfilled due to the increased error rate.

## Detection and mitigation
- The incident was detected through automated monitoring alerts indicating a critical rise in error rates.
- Mitigation steps included restarting the unhealthy pods and rolling back the deployment that introduced the configuration issue, both of which contributed to resolving the error rate spike.
- Follow-up actions proposed include implementing deployment-time validation for critical configuration flags to prevent similar issues in future releases, in addition to considering a lower canary deployment threshold.

## Root cause analysis  
The root cause of the checkout-api incident was a misconfiguration during the deployment process, specifically the setting of the PAYMENTS_RETRY_MAX config flag to 0, which directly resulted in an increased error rate and failure of checkout transactions. The error rate exceeded 5%, triggering automated monitoring alerts that allowed for the incident to be identified relatively swiftly.

### Proximate Trigger
- The immediate trigger was the deployment of a release that contained the configuration error (PAYMENTS_RETRY_MAX set to 0). This caused checkout transactions to fail, leading to spikes in error rates.

## Contributing factors  
1. **Lack of Configuration Validation:** There was no pre-deployment validation mechanism to check critical configuration flags, which could have prevented the faulty deployment.
2. **Canary Deployment Threshold:** The existing canary deployment strategy only tested 10% of users. This volume may not have been sufficient to uncover the bug before impacting a larger audience.
3. **Monitoring Limitations:** The speed of detection did not prevent the initial impact caused by the configuration error. Enhancement opportunities exist for monitoring systems to detect more subtle issues before they escalate.
4. **Pod Management Response Time:** Restarting the unhealthy pods provided only a temporary respite, as the root cause remained unaddressed until the rollback occurred. Better incident response protocols could be established to reset or manage faulty services while investigating their underlying issues.

## What went well  
- **Effective Monitoring and Alerts:** The incident was detected promptly via automated alerts when the error rate exceeded critical thresholds, allowing for a quick response.
- **Swift Rollback Procedure:** The rollback of the deployment was executed effectively, resulting in normalized operations within minutes and demonstrating effective incident management protocols.
- **No Data Loss:** Despite the spike in error rates resulting in failed transactions, there was no data loss, indicating robust data management practices even in incidents of service disruption.

## Action items
1. **Deployment Engineer**: Implement deployment-time validation for all critical configuration flags. Success will be verified by a reduction of misconfigured deployments. **[TBD]**
2. **DevOps Team**: Reassess and potentially lower the canary deployment threshold to 5% or expand monitoring during initial phases. Success will be verified by fewer post-deployment service incidents. **[TBD]**
3. **Incident Response Team**: Establish enhanced pod management protocols that include pre-checks for known configuration errors. Success will be verified by reducing response time to similar incidents. **[TBD]**
4. **Monitoring Team**: Enhance monitoring systems to detect slower-rising issues before they become critical. Success will be defined by reduction in the average time from incident detection to impact. **[TBD]**

## What we learned
The incident underscored the critical importance of validating configuration settings prior to deployment and highlighted the necessity of improving incident response protocols. Additionally, it reaffirmed the value of robust monitoring systems and the need for thorough testing techniques to prevent faulty configurations from impacting users. By implementing the identified action items, we aim to ensure smoother deployments and a better customer experience in the future.