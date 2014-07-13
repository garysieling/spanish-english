import nltk
import codecs
import pickle

en_lines = [line.decode('utf8').strip() for line in open('en.txt')]
sp_lines = [line.decode('utf8').strip() for line in open('sp.txt')]

def para(lines):
  para = ''
  for l in lines:
    para = para + ' ' + l
    if l == '':
      yield para.strip()
      para = ''

en_para = [x for x in para(en_lines)]
sp_para = [x for x in para(sp_lines)]

pickle.dump(en_para, open('_en_para', 'wb'))
pickle.dump(sp_para, open('_sp_para', 'wb'))

def flatten(l):
  out = []
  for item in l:
    if isinstance(item, (list, tuple)):
      out.extend(flatten(item))
    else:
      out.append(item)
  return out

en_sp = {}
def read_dict(file_name):
  dict = [line.strip() for line in codecs.open(file_name, 'r', 'utf-8')]
  for l in dict:
    words = l.split("\t")
    if len(words) < 2:
      continue

    # dictionary shows synonyms
    en_words = [w.strip() for w in words[0].split(";")]
    sp_words = [w.strip() for w in words[1].split(";")]

    # discard parts of speech and handle synonyms
    #sp_words = flatten([w.split('-')[-1].split(";") for w in words[1:]])
    #sp_words = [w.strip().lower() for w in sp_words]

    print "English: "
    print en_words
 
    print "Spanish:"
    print sp_words
 
    for e in en_words:
      e_l = e.lower()
      if (e_l in en_sp):
        en_sp[e_l] = list(set(en_sp[e_l] + sp_words))
      else:
        en_sp[e_l] = sp_words

read_dict('dict.txt')
read_dict('dict2.txt')
read_dict('dict3.txt')

_en_sp = open('_en_sp', 'w')
_en_sp.write(unicode(en_sp))
_en_sp.close()

found = 0
total_tokens = 0

def transliterate(en_tokens, sp_tokens, lower_sp):
  global found
  global total_tokens

  final_tokens = []
  for w in en_tokens:
    #print w
    token = w

    if (stopword(w)):
      pass 
    else:
      total_tokens = total_tokens + 1    
 
    w_l = w.lower()
    if (w_l in en_sp):
      candidates = en_sp[w_l]
      #print "Candidates:"
      for c in candidates:
        #print c
        if c in lower_sp:
          #print "<SUITABLE TRANSLATION FOUND>"
          token = c
          found = found + 1
        else:
          pass
          #print "not available" 
    else:
      pass
      #print "Not in dictionary"
    
    final_tokens.append(token)
  return ' '.join(final_tokens)

import nltk

def transliterate_all(en_para, sp_para, idx):
  para_en = en_para[idx]
  para_sp = sp_para[idx]

  en_tokens = nltk.word_tokenize(para_en)
  sp_tokens = nltk.word_tokenize(para_sp)

  lower_sp = [w.lower() for w in sp_tokens]

  #print en_tokens
  #print ""
  #print sp_tokens
  #print ""

  #print para_en
  #print ""
  #print para_sp
  #print ""
  t = transliterate(en_tokens, sp_tokens, lower_sp)

def stopword(w):
  import re
  if (w in ['.', ',', '``', ':', ';', '?', '!', '"', "''", '}', '{']):
    return True

  if (re.match('^\d+$', w)):
    return True

  return False

def build_dict():
  def find_missing(en_tokens, sp_tokens, lower_sp):
    missing = []
    for w in en_tokens:
      if (stopword(w)):
        pass 
 
      w_l = w.lower()
      if (w_l in en_sp):
        candidates = en_sp[w_l]
        for c in candidates:
          if c in lower_sp:
            pass 
          else:
            missing.append(w_l)
      else:
        missing.append(w_l)
  
    return missing

  unique_counts = {} 
  frq_en = {}
  frq_sp = {}

  def learn_dict(en_para, sp_para, idx):
    para_en = en_para[idx]
    para_sp = sp_para[idx]

    en_tokens = nltk.word_tokenize(para_en)
    sp_tokens = nltk.word_tokenize(para_sp)

    lower_en = [w.lower() for w in en_tokens]
    lower_sp = [w.lower() for w in sp_tokens]

    missing = find_missing(en_tokens, sp_tokens, lower_sp)

    for w in missing:
      if w in frq_en: 
        frq_en[w] = frq_en[w] + 1
      else: 
        frq_en[w] = 1

    for w in lower_sp:
      if w in frq_sp: 
        frq_sp[w] = frq_sp[w] + 1
      else:
        frq_sp[w] = 1

    missing = find_missing(en_tokens, sp_tokens, lower_sp)
    for en in set(missing):
      if stopword(en):
        continue 

      for sp in set(lower_sp):
        if stopword(sp):
          continue
        
        key = en + '_' + sp
        c = 0
        if (key in unique_counts):
	  (_en, _sp, c) = unique_counts[key]
        
        unique_counts[key] = (en, sp, c + 1)
 
  for idx in range(0, min(len(en_para), len(sp_para))):
    learn_dict(en_para, sp_para, idx)
 
  filtered = []
  sorted_counts = sorted(unique_counts.values(), key=lambda x: x[2], reverse = True)
  found_count = 0
  for (en, sp, c) in sorted_counts:
    f_en = frq_en[en]
    f_sp = frq_sp[sp]
    ratio = max(1.0 * f_en / f_sp, 1.0 * f_sp / f_en)
    if (c > 1 and ratio < 1.01 and found_count < 25):
      if (en in en_sp):
        if (sp in en_sp[en]):
          continue

      print en + "\t" + sp + " %.0f, %.2f, %.2f, %.2f" % (c, f_en, f_sp, ratio)
      #filtered.append((en, sp, c, f_en, f_sp, ratio))
      found_count = found_count + 1
 
  return filtered

print build_dict()

for idx in range(0, min(len(en_para), len(sp_para))):
  transliterate_all(en_para, sp_para, idx)

print "Percent replaced: %.2f (%.0f, %.0f)" % (100 * found / total_tokens, found, total_tokens)
