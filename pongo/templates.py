error_template = """
<html>
<head>
<title>Error</title>
<style type="text/css">
body {
font-family: sans-serif;
}
a.button {
display: inline-block;
border: 1px solid #0000e0;
background-color: #0000e0;
color: white;
border-radius: 15px;
text-decoration: none;
padding: 5px;
width: 150px;
}
h1, h2, div {
text-align: center;
}
h2 {
font-size: 20px;
}
div{
margin-top: 40px;
}
</style>
</head>
<body>
<h1>So Sorry!</h1>
<h2>Could not connect to %s.</h2>
<div>
<a class="button" href="http://%s/albums/">Try again</a>
</div>
<div>
<a class="button" href="http://load.error/pongo/connect">Go Back</a>
</div>
</body>
</html>
"""
