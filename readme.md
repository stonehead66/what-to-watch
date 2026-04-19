# WHAT TO WATCH?!
#### Video Demo:  <URL https://youtu.be/0cTDehLQCJU>
#### Description:
Have you ever wanted to watch a movie, but didn't know which one or couldn't find a suitable one? Me too - a lot! So I decided to make a web app which helps with this issue as my final project of the CS50 course: What to watch?!

#### What does it do?
You answer 4 simple questions concerning the max. age, genre, language and rating you want your movie to have. You choose between one or more of the shown options/buttons (depending on the question) or "skip". After that you get your movie recommendation. On the result-page you also have links to youtube (trailer search) and to imdb and tmdb. There is also a button which gives another movie recommendation based on the given choices. You can see those also on the result-page. As a gimmick, a - hopefully somewhat funny - movie meme pops up in between the questions.

#### How does it work?
I used python and flask with a SQL database as backend. The database was created with a free dataset from Internet Movie Database (IMDb) as a basis and additional information on spoken languages from The Movie Database (TMDB) which where obtained via API calls. Furthermore, I did some data cleaning, f.e. remove all movies with less then 500 ratings and remove all series.

In app.py a parameters dictionary (rec_param) is created to save the choices/parameters of the user. 


Javascript, css, 




TODO

If unfamiliar with Markdown syntax, you might find GitHub’s Basic Writing and Formatting Syntax helpful. You can also preview your .md file by clicking the ‘preview’ icon as explained here: Markdown Preview in vscode. Standard software project READMEs can often run into the thousands or tens of thousands of words in length; yours need not be that long, but should at least be several hundred words that describe things in detail!

Your README.md file should be minimally multiple paragraphs in length, and should explain what your project is, what each of the files you wrote for the project contains and does, and if you debated certain design choices, explaining why you made them. Ensure you allocate sufficient time and energy to writing a README.md that documents your project thoroughly. Be proud of it! A README.md in the neighborhood of 750 words is likely to be sufficient for describing your project and all aspects of its functionality. If unable to reach that threshold, that probably means your project is insufficiently complex.

Execute the submit50 command below from within your project directory (or from whichever directory contains README.md file and your project’s code, which must also be submitted), logging in with your GitHub username and password when prompted. For security, you’ll see asterisks instead of the actual characters in your password.

submit50 cs50/problems/2025/x/project








