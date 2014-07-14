import nltk
import codecs
import pickle
import re
import operator

en_lines = [line.decode('utf8').strip() for line in open('en.txt')]
sp_lines = [line.decode('utf8').strip() for line in open('sp.txt')]

# used in a few places later on...
from nltk.stem import SnowballStemmer

en_stemmer = SnowballStemmer("english")
sp_stemmer = SnowballStemmer("spanish")

def para(lines):
  comment_block = re.compile('{[^}]*}', flags=re.IGNORECASE)
  digit_block = re.compile('^[0-9]+ ', flags=re.IGNORECASE)
  negative_block = re.compile("n't ", flags=re.IGNORECASE)
  plural_block = re.compile("'s", flags=re.IGNORECASE)

  para = ''
  for l in lines:
    para = para + ' ' + l
    if l == '':
      # one of the books I tested used notes in brackets
      # to write in commentary, which was unhelpful
      para = para.strip()

      para = digit_block.sub('', para)
      para = comment_block.sub(' ', para)
      para = negative_block.sub(' not ', para)
      para = plural_block.sub('s', para)
      yield para.strip()
      para = ''

en_para = [x for x in para(en_lines)]
sp_para = [x for x in para(sp_lines)]

#pickle.dump(en_para, open('_en_para', 'wb'))
#pickle.dump(sp_para, open('_sp_para', 'wb'))

def flatten(l):
  out = []
  for item in l:
    if isinstance(item, (list, tuple)):
      out.extend(flatten(item))
    else:
      out.append(item)
  return out

# There are two dictionaries here. One is a raw word
# mapping, the other is stemmed word mappings.
en_sp = {}
en_sp_stem = {}

def read_dict(file_name):
  def stem_all(stemmer, list):
    return [stemmer.stem(w) for w in list]

  dict = [line.strip() for line in codecs.open(file_name, 'r', 'utf-8')]
  for l in dict:
    words = l.split("\t")
    if len(words) < 2:
      continue

    # dictionary shows synonyms as a comma separated list
    en_words = [w.strip().lower() for w in words[0].split(";")]
    sp_words = [w.strip().lower() for w in words[1].split(";")]

    # discard parts of speech and handle synonyms
    #sp_words = flatten([w.split('-')[-1].split(";") for w in words[1:]])
    #sp_words = [w.strip().lower() for w in sp_words]

    #print "English: "
    #print en_words
 
    #print "Spanish:"
    #print sp_words

    for e in en_words:
      e_l = e.lower()

      e_l_stem = en_stemmer.stem(e_l)

      # this complexity is because we want to support multiple
      # dictionary files, which may have duplicates, and because
      # we want the relationship between words in the two languages
      # to be many to many
      if (e_l in en_sp):
        en_sp[e_l] = list(set(en_sp[e_l] + sp_words))
      else:
        en_sp[e_l] = sp_words

      if (e_l_stem in en_sp_stem):
        en_sp_stem[e_l_stem] = list(set(en_sp_stem[e_l_stem] + stem_all(sp_stemmer, sp_words)))
      else:
        en_sp_stem[e_l_stem] = stem_all(sp_stemmer, sp_words)


read_dict('dict.txt')
read_dict('dict2.txt')
read_dict('dict3.txt')
read_dict('dict5.txt')
read_dict('dict6.txt')
read_dict('dict8.txt')

_en_sp = open('_en_sp', 'w')
_en_sp.write(unicode(en_sp))
_en_sp.close()

found = 0
total_tokens = 0

not_found = {}
def transliterate(en_tokens, sp_tokens, en_sentence, sp_sentence, lower_sp):
  global found
  global total_tokens
  global not_found

  final_tokens = []
  para_solved = True
  sentence_tokens = 0
  sentence_found = 0

  for w in en_tokens:
    #print w
    token = w.strip()

    if (w.endswith(',') or w.endswith('.')):
      w = w[:-1]

    if (len(w) == 0):
      continue

    if (noise_token(w)):
      continue 
    else:
      total_tokens = total_tokens + 1
      sentence_tokens = sentence_tokens + 1
 
    w_l = w.lower()
    found_mapping = False

    # check to see if one of the dictionaries has an exact match
    if (w_l in en_sp):
      candidates = en_sp[w_l]
      #print "Candidates:"
      for c in candidates:
        #print c
        if c in lower_sp:
          #print "<SUITABLE TRANSLATION FOUND>"
          token = c
          found_mapping = True
        else:
          pass
          #print "not available" 
    else:
      pass
      #print "Not in dictionary"
   
    w_l_stem = en_stemmer.stem(w_l)
    lower_sp_stem = [sp_stemmer.stem(w_sp) for w_sp in lower_sp]
    if (not found_mapping):
      if (w_l_stem in en_sp_stem):
        candidates = en_sp_stem[w_l_stem]
        #print "Candidates:"
        for c in candidates:
          #print c
          if c in lower_sp_stem:
            #print "<SUITABLE TRANSLATION FOUND USING STEMMING>"
            token = lower_sp[lower_sp_stem.index(c)]
            found_mapping = True
          else:
            pass
            #print "not available" 
      else:
        pass
        #print "Not in dictionary"
     
    if (found_mapping):
      found = found + 1
      sentence_found = sentence_found + 1
    else:
      if (w_l in lower_sp):
        found = found + 1
        sentence_found = sentence_found + 1
      else:
        para_solved = False
        if (not w_l in not_found):
          not_found[w_l] = 1
        else:
          not_found[w_l] = not_found[w_l] + 1
 
    if (w[0].isupper()):
      token = token.capitalize()
 
    final_tokens.append(token)
  return (' '.join(final_tokens), para_solved, sentence_found, sentence_tokens)

import nltk

def transliterate_all(en_para, sp_para, idx):
  para_en = en_para[idx]
  para_sp = sp_para[idx]

  en_tokens = nltk.word_tokenize(para_en)
  sp_tokens = nltk.word_tokenize(para_sp)

  lower_sp = [w.lower() for w in sp_tokens]

  (t, para_mapping, para_found, para_tokens) = transliterate(en_tokens, sp_tokens, para_en.lower(), para_sp.lower(), lower_sp)

  found_missing = False
  look_at = ['gatekeeper', 'consider', 'worshiped', 'follow', 'oldest', 'disobeys', 'simon', 'disciples', 'young', 'asking', 'arisen', 'under', 'women', 'worth', 'seized', 'parcel', 'advantage', 'sitting', 'print', 'accuse', 'advised', 'isaiah', 'continued', 'perceived', 'joined', 'leave', 'force', 'awake', 'yourself', 'sabbath', 'denarii', 'abroad', 'stands', 'advantageous', 'assembled', 'rhabbouni', 'learned', 'ever', 'forgive', 'observing', 'completely', 'accomplished', 'descended', 'salvation', 'hosanna', 'cloak', 'decrease', 'guests', 'few', 'live', 'fragrance', 'knows', 'holy', 'porch', 'brings', 'testified', 'retained', 'midst', 'hold', 'name:', 'account', 'metretes', 'embarked', 'believes', 'outran', 'gathers', 'murmuring', 'loosen', 'council', 'mixture', 'caused', 'court', 'winter', 'lame', 'rather', 'following', 'permission', 'shining', 'surpassed', 'lamp', 'pure', 'dared', 'speaks', 'beach', 'questioning', 'mother', 'law', 'revealed', 'capernaum', 'lifting', 'branches', 'waist', 'whenever', 'loud', 'sit', 'eats', 'bathed', 'or', 'began', 'interpretation', 'decide', 'toward', 'choose', 'held', 'already', 'looks', 'brim', 'existence', 'jacobs', 'bringing', 'torn', 'brook', 'better', 'maid', 'farmer', 'hidden', 'overcome', 'seeking', 'often', 'prunes', 'flee', 'bread', 'execute', 'hereafter', 'servant', 'tear', 'leaned', 'burial', 'doing', 'stooping', 'flock', 'tenth', 'blinded', 'special', 'shown', 'since', 'washed', 'testify', 'looking', 'lain', 'gardener', 'foundation', 'turning', 'commits', 'seventh', 'surely', 'worshipper', 'overtake', 'cured', 'prepare', 'rejects', 'keep', 'bridegroom', 'thing', 'expedient', 'retain', 'first', 'plainly', 'spoken', 'wash', 'open', 'sheep', 'twisted', 'needed', 'too', 'passed', 'john', 'fifty-three', 'sealed', 'cheer', 'part', 'feeds', 'porches', 'bride', 'determined', 'insulted', 'donkey', 'groaning', 'remained', 'ran', 'suspense', 'manner', 'recover', 'convicts', 'afraid', 'overthrew', 'self', 'able', 'rowed', 'enlightens', 'sure', 'risen', 'commanding', 'flow', 'yours', 'perceiving', 'donkeys', 'agreed', 'large', 'soldiers', 'find', 'ground', 'true', 'distributed', 'enough', 'defiled', 'treasury', 'colt', 'listened', 'beat', 'enters', 'rejoices', 'ones', 'hid', 'breast', 'altogether', 'during', 'reveal', 'showed', 'fields', 'insane', 'testing', 'relative', 'seal', 'draws', 'tend', 'written', 'finger', 'correctly', 'drawn', 'burned', 'counsel', 'lays', 'gives', 'men', 'crucified', 'precious', 'grieved', 'mans', 'reported', 'freely', 'invited', 'became', 'groaned', 'whole', 'point', 'legs', 'pot', 'withered', 'pruned', 'vessel', 'table', 'trust', 'withdrawn', 'olives', 'stretch', 'three', 'convicted', 'secret', 'cords', 'mary', 'lived', 'perplexed', 'offers', 'finished', 'lift', 'personally', 'fellow', 'homes', 'myself', 'save', 'publicly', 'sanctify', 'straight', 'taking', 'purifying', 'demon', 'hebrew', 'ready', 'happening', 'multitudes', 'containing', 'dishonor', 'cross', 'tells', 'stepped', 'used', 'booths', 'drink', 'upon', 'moving', 'supposing', 'warming', 'destruction', 'dark', 'bondage', 'makes', 'possessed', 'finds', 'sychar', 'without', 'greatest', 'dressed', 'drawing', 'stooped', 'rolled', 'aside', 'foot', 'world', 'sandal', 'cup', 'rose', 'drunk', 'arrest', 'belongs', 'crying', 'prison', 'struck', 'remaining', 'ought', 'zion', 'kills', 'read', 'possible', 'birth', 'bit', 'reap', 'name', 'lost', 'sincerely', 'serves', 'pavement', 'steps', 'officer', 'lose', 'whomever', 'heel', 'wonders', 'snatches', 'old', 'jews', 'authority', 'daylight', 'scatters', 'sight', 'perfected', 'delivered', 'paralyzed', 'oppression', 'forgiven', 'convict', 'temple', 'murderer', 'itself', 'sixth', 'trees', 'bury', 'urged', 'stand', 'act', 'tomb', 'basin', 'burning', 'anothers', 'son', 'jerusalem', 'stench', 'existed', 'beneath', 'exposed', 'peters', 'dispersion', 'pool', 'forward', 'golgotha', 'head', 'form', 'immorality', 'cloth', 'hail', 'trying', 'tossed', 'skull', 'until', 'stirring', 'educated', 'father-in-law', 'sheath', 'dragging', 'proceeds', 'fill', 'conspired', 'sexual', 'peace', 'evildoer', 'sick', 'sufficient', 'journey', 'earthly', 'else', 'thundered', 'together', 'glorify', 'apart', 'profits']
  en_l = [w.lower() for w in en_tokens]
  for w in look_at:
    if (w in en_l):
      found_missing = True

  if (1.0 * para_found / para_tokens < 0.5 and found_missing):
    print "Rate: %.0f / %.0f -> %.2f" % (para_found, para_tokens, 100.0 * para_found / para_tokens)
    print para_en.encode('utf-8')
    print para_sp.encode('utf-8')
    print ""
    # apply some minor visual corrections
    t = t.encode('utf-8')
    t = t.replace(' .', '.')
    t = t.replace(' ,', ',')

    print t
    print ""
    print ""

def noise_token(w):
  if (w in ['.', ',', '``', ':', ';', '?', '!', '"', "''", "'", '}', '{', ')', '(', '-', '--']):
    return True

  if (re.match('^\d+$', w)):
    return True

  return False

def build_dict():
  def find_missing(en_tokens, sp_tokens, lower_sp):
    missing = []
    for w in en_tokens:
      if (noise_token(w)):
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
      if noise_token(en):
        continue 

      for sp in set(lower_sp):
        if noise_token(sp):
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

      #print en + "\t" + sp + " %.0f, %.2f, %.2f, %.2f" % (c, f_en, f_sp, ratio)
      #filtered.append((en, sp, c, f_en, f_sp, ratio))
      found_count = found_count + 1
 
  return filtered

#print build_dict()

for idx in range(0, min(len(en_para), len(sp_para))):
  transliterate_all(en_para, sp_para, idx)

print "Percent replaced: %.2f (%.0f, %.0f)" % (100 * found / total_tokens, found, total_tokens)

for (k, v) in sorted(not_found.iteritems(), key=operator.itemgetter(1)):
  print "%s: %.0f" % (k, v)
