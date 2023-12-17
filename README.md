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
- The index.html makes a call to the Lambda API, which increments the visit counter stored in DynamoDB by +1.<br>
- I receive the visit count from the API and display it by updating the value of the visits field using JavaScript.<br>
<br>

<h2>Functions not shown:</h2>
- Any push to Main branch will trigger the GitHub actions and, using the secret credentials of a user with permissions restricted to only this project, it uploads the modified files to the S3 bucket.<br>
- When I run 'terraform apply', a Lambda function is created with the necessary permissions to access the specified database, enabling a URL that can be executed from the S3 bucket.
