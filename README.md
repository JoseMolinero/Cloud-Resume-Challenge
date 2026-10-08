<h1>Cloud Resume Challenge</h1>
This project is my online resume, a static web page, serving simple html & css with the help of some <a href="https://html5up.net">templates </a>

You can visit my domain here: [josemolinero.com](https://josemolinero.com)

<h2>Project scheme:</h2>
<img src = "https://github.com/JoseMolinero/Cloud-Resume-Challenge/blob/master/images/Esquema.png"/>
<br>

<h2>How the project works for the user:</h2>
- The user searches for the domain josemolinero.com.<br>
- Route 53 redirects them to the CloudFront distribution associated.<br>
- CloudFront serves the index.html from the associated S3 bucket.<br>
- The index.html calls the Lambda API, which records the connection IP in DynamoDB and increments the visit counter by +1.<br>
- I receive the visit count from the API and display it by updating the value of the visits field using JavaScript.<br>
<br>

<h2>Deployment:</h2>

- Pushes to `master` deploy only the HTML, CSS, JavaScript, fonts and images used by the site. The workflow deletes stale objects from the site bucket and invalidates only uploaded or deleted CloudFront paths. An `index.html` change also invalidates `/`.
- The workflow assumes an AWS IAM role through GitHub OIDC. Configure the `AWS_DEPLOY_ROLE_ARN`, `AWS_S3_BUCKET` and `CLOUDFRONT_DISTRIBUTION_ID` repository secrets before running it. The role trust policy must restrict GitHub to this repository and the `master` branch. It needs `s3:ListBucket` on the site bucket, `s3:PutObject` and `s3:DeleteObject` on its objects, and `cloudfront:CreateInvalidation` on the distribution. Remove the old long-lived AWS access-key secrets after OIDC is working.
- The S3 origin already shows an origin-access ID in CloudFront, but confirm whether it is OAC or legacy OAI and whether the S3 bucket policy grants it read access before the first deploy without `public-read`. Migrate to OAC if necessary, then block direct public S3 access. Review the bucket contents before the first run because `--delete` removes objects outside the site's explicit file set.
- `terraform apply` in `infra/` updates the Lambda runtime and counter permissions. The DynamoDB `visitas` table must have a string partition key named `id`; `direcciones` must have a string partition key named `ip`. Terraform generates `packedlambda.zip` locally; it is not committed.

<h2>Visit details:</h2>

- Lambda takes the IP from `requestContext.http.sourceIp`, not from browser input. The `direcciones` item for each IP stores `first_seen`, `last_seen`, `visits`, and `expires_at`. By default, the retention period is 180 days since the last visit; set `ip_retention_days` in Terraform to change it and update the notice in `index.html` to match. **Enable DynamoDB TTL on the `expires_at` attribute** for old items to be deleted (`aws dynamodb update-time-to-live --table-name direcciones --time-to-live-specification Enabled=true,AttributeName=expires_at --region eu-west-2`). DynamoDB can take a few days to remove expired items. Existing items without `expires_at` need a separate cleanup. This table aggregates visits by IP; it is not a record of every individual page request.
- The public Lambda URL currently receives requests directly, so country and region are not available from CloudFront. To add them, create a Lambda URL origin and a non-cached API behavior in this distribution, forward `CloudFront-Viewer-Address`, `CloudFront-Viewer-Country` and `CloudFront-Viewer-Country-Region` through an origin request policy, protect that origin with Lambda OAC and `AWS_IAM`, then switch the browser to the CloudFront API path and set `trust_cloudfront_headers = true`. Keep it `false` while the URL is public: callers could forge those headers. AWS requires a SHA256 payload header for `POST` requests routed through Lambda OAC.
- The function URL is still publicly invokable. CORS and reserved concurrency reduce exposure but do not authenticate callers. CloudFront standard access logs can complement this table because they capture requests even when JavaScript does not run. An IP or geographic region cannot identify a particular person or employer reliably. Since IP addresses are personal data, publish an appropriate privacy notice and check the legal basis and retention for this analytics use.

To validate the counter locally, run `python -m unittest discover -s tests`. To validate the infrastructure, run `terraform -chdir=infra init` and `terraform -chdir=infra validate` with a current Terraform CLI. Commit the generated `infra/.terraform.lock.hcl` after reviewing the selected provider versions.

AWS setup references: [GitHub OIDC](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws), [S3 OAC](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html), [Lambda URL OAC](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-lambda.html).
