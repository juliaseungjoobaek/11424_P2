# 11424_Project 2

The Second Project
 

The goal of the second project is to generate the inflectional forms of verbs for Karbardian (kbd), Swahili (swc), and Mixtec (sty) from roots + inflectional information better than non-neural and neural baselines.

 

Prerequisite Reading
You must go through the following chapter in the book thoroughly before beginning this project. (Maybe?) it contains some really useful hints ;)

inflections.pdfDownload inflections.pdf
 

The data
You willl be provided with data from three languages:

Kabardian [kbd], a language primarily spoken in the North Caucases and written in Cyrillic.
Swahili [swc], a language primarily spoken along the East African coast and written in a Latin script.
Mixtec [xty], a language primarily spoken in Mexico and written in a Latin script in our dataset.
For each language, you will be provided with train, dev, and test files. Files are formatted in the unimorph standard, with the exception of the testset where the correct forms are omitted: [ROOT] ([CORRECT]) [INFLECTION]

dataset.zip
 

The task
You are expected to produce correct inflected forms for each line in the testset. Please name your files as {lang}.txt - i.e. kbd.txt - for submission to the autograder. You submission will be a list of generated forms seperated by newlines for each language. The baseline scores to beat are as follows:

Screenshot 2025-02-11 at 13.27.08.png

 

The code to reproduce the baseline can be found here
