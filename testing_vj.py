import datetime
import string
print("hello")

datet1=datetime.datetime.now()
datetime1=str(datet1).split(" ")[1]
#print(datetime1 )
datetime1="13:00:00"
hr=int(datetime1.split(":")[0])
mm=int(datetime1.split(":")[1])
ss=datetime1.split(":")[2]
ss=ss[:2]
ss=int(ss) 
hr="Good Night" if(hr>=12 and mm>=00 and ss>=00) else "Good Morning"
print(hr)


