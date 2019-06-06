import markovify

with open('texts_2') as f:
    text = f.read()

m = markovify.Text(text)

for i in range(5):
    print(m.make_sentence())
