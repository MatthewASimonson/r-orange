from OWRpy import *



dataFrame_name = 'd1'
#dataFrame = self.r('d1= read.delim("I:/Python25/Lib/site-packages/orange/OrangeCanvas/analysis.txt",na.strings="NA")')
dataFrame = r('d1= read.delim("F:/user data/Documents/lab/solexa/paper/data files/analysis.txt",na.strings="?")')

data = convertDataframeToExampleTable(dataFrame)

# col_names = r.colnames(dataFrame)
# col_def = r.sapply(dataFrame,'class')

# colClasses = []
# for i in col_names:
	# if col_def[i] == 'numeric' or col_def[i] == 'integer':
		# colClasses.append(orange.FloatVariable(i))
	# elif col_def[i] == 'factor':
		# colClasses.append(orange.StringVariable(i))
	# elif col_def[i] == 'character':
		# colClasses.append(orange.StringVariable(i))



# d = r('as.matrix(d1)')
# domain = orange.Domain(colClasses)
# data = orange.ExampleTable(domain, d)		


#d = r('d1 = data.frame(b1=c(1,2,5),a2=c("a","b","c"))')