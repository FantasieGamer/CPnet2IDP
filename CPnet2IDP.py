import xml.etree.ElementTree as ET
import sys

# Check for all arguments and extensions
if (len(sys.argv) < 4) or not sys.argv[1].endswith('.idp') or not sys.argv[2].endswith('.xml') or not sys.argv[3].endswith('.idp'):
    sys.exit('Use: Main.py <IDP-file> <CPNet-XML-file> <Output-file>')

# Open files
i_idp = open(sys.argv[1], 'r')
cpnet =  ET.parse(sys.argv[2])
o_idp = open(sys.argv[3], 'w')

# Ask user for function-name and list of types for cost-relation
fname = input("Geef functienaam die door inferentie ingevuld wordt(bv. in te vullen uurrooster):")
costlist = input("Geef de types (gescheiden door komma's) waarop de kost van toepassing is (bv. per persoon):")
basecost = input("Wat is de kost van een overtreding?:")

costlist = costlist.split(',')

# Find vocabulary specification in CP-net XML-file
vars = cpnet.findall('PREFERENCE-VARIABLE')
for pref_var in vars:
    if pref_var[0].text == 'VOC':
        voc_list = []
        for voc_elem in pref_var.findall('DOMAIN-VALUE'):
            voc_list.append(voc_elem.text)

# Copy vocabulary from input IDP-file to Output
flag = False
for line in i_idp:
    if ('vocabulary' in line) or flag:
        flag = True
        # Save vocabulary name
        if 'vocabulary' in line:
            voc_name = line.split('{')
            voc_name = voc_name[0].lstrip()
            voc_name = voc_name[11:]
        if "}" not in line:
            if fname in line:
                fullfname = line
            o_idp.write(line)
        else:
            o_idp.write("    type Order isa int\n")
            o_idp.write("    type Cost isa int\n")
            vocline = "    PreferList("
            for i, v_elem in enumerate(voc_list):
                vocline += v_elem
                if i+1 < len(voc_list):
                    vocline += ', '
            o_idp.write(vocline+")\n")
            vocline = "    Prefer("
            for v_elem in voc_list:
                vocline += (v_elem + ", ")
            o_idp.write(vocline+"Order)\n")
            vocline = "    PreferFull("
            for v_elem in voc_list:
                vocline += (v_elem + ", ")
            o_idp.write(vocline+"Order)\n")
            vocline = "    PreferCost("
            for costl in costlist:
                vocline += (costl + ', ')
            o_idp.write(vocline+" Cost)\n")
            o_idp.write(line)

            flag = False
i_idp.close()

# find "usable info" about preferences (last lvl of each group of nodes)
pref_info = []
pref_ids = []
prefs = cpnet.findall('PREFERENCE-STATEMENT')
for pref in prefs:
    if pref[1].text.partition('_')[0] != "VOC":
        pref_ids.append([pref[0].text.partition('_')[0],pref[1].text.partition('_')[0]])
cnt = 0
prev_var = "null"
prev_item = "null"
for i, pref in enumerate(pref_ids):
    # if previous is empty (just started) or letter is same, but different version
    if prev_var == "null" or (prev_var[1] == pref[1] and prev_var[0] != pref[0]):
        prev_var = pref
    else:
        # if current letter is different from last added, reset counter
        if prev_item[1] != pref[1]:
            cnt = 0
        # if letter is the same and version is different from last added,
        # remove "cnt" previous + reset counter
        if prev_item[1] == prev_var[1] and prev_item[0] != prev_var[0]:
            for x in range(cnt):
                pref_info.pop()
            cnt = 0
        pref_info.append(prefs[i-1])
        cnt += 1
        prev_item = prev_var #Remember last added info (to check for useless info)
        prev_var = pref
pref_info.append(prefs[i]) #Add last block as well

# Function for recursive filling of emitted specs
def fillspecs(missing_voc_term_list, i, preferLine):
    for missing_val in speclist[missing_voc_term_list[i]]:
        specobj[missing_voc_term_list[i]] = missing_val
        # End of the list?
        if (i+1) != len(missing_voc_term_list):
            fillspecs(missing_voc_term_list, i+1, preferLine)
        else:
            # Print line into IDP out-file
            preferLine = ""
            for voc_item in voc_list:
                o_idp.write(specobj[voc_item] + ', ')
                preferLine += (specobj[voc_item] + ', ')
            o_idp.write(specobj['Order'] + '; ')
            preferLine = preferLine.rstrip(', ') + '; '
            preferList.append(preferLine)



# Start copying Structure from IDP input-file and add specification info
i_idp = open(sys.argv[1], 'r')
flag = False
readmode = False
speclist = {}
read_voc_term = 'null'
preferList = []
for v_t in voc_list:
    speclist[v_t] = []
for line in i_idp:
    if ('structure' in line) or flag:
        flag = True
        # Save structure name
        if 'structure' in line:
            str_name = line.split(':')
            str_name = str_name[0].lstrip()
            str_name = str_name[10:]
        if line.strip() != "}":
            if readmode:
                # Line is more specs info
                for spec_term in line.split(';'):
                    speclist[read_voc_term].append(spec_term.strip('{ }\n'))
                if '}' in line:
                    # End reached, no further specs for this type
                    readmode = False
                    read_voc_term = 'null'
            else:
                # Check if specification begins
                for voc_term in voc_list:
                    if voc_term in line:
                        if "}" not in line:
                            readmode = True # Need to read more than one line for all specs
                            read_voc_term = voc_term
                            splitline = line.partition('=')
                            allspecs =  splitline[2]
                            speclist[voc_term] = []
                            for spec_term in splitline[2].split(';'):
                                speclist[voc_term].append(spec_term.strip('{ }\n'))
                        else:
                            # All specs in one line
                            splitline = line.partition('=')
                            allspecs =  splitline[2]
                            speclist[voc_term] = []
                            for spec_term in splitline[2].split(';'):
                                speclist[voc_term].append(spec_term.strip('{ }\n'))
            # write line to out-file
            o_idp.write(line)

        else:
            # At the end, insert new relation specification
            o_idp.write('    Prefer = {')
            for pref_stat in pref_info:
                specobj = {}
                # Find which voc type information is about
                for key, value in speclist.items():
                    if pref_stat[1].text.partition('_')[0] in value:
                        specobj[key] = pref_stat[1].text.partition('_')[0]
                # Go find cost/order for this preference by searching through all preferences
                cond_list = pref_stat.findall('CONDITION')
                cost = 0
                # not empty list
                if cond_list:
                    for cond in cond_list:
                        for cond_pref in prefs:
                            wrong = True
                            found = False
                            # Check if name is right
                            if cond_pref[1].text == cond.text.partition('=')[0]:
                                cond_pref_list = cond_pref.findall('CONDITION')
                                if cond_pref_list:
                                    # Check if same values for conditions
                                    for each_cond in cond_pref_list:
                                        for ct_lst in cond_list:
                                            if each_cond.text == ct_lst.text:
                                                wrong = False
                                                break
                                    if not wrong:
                                        # Found right preference -> check value of cost
                                        found = True
                                        for y, pref_val in enumerate(cond_pref.findall('PREFERENCE')):
                                            if ':' not in pref_val.text:
                                                break
                                            if pref_val.text.split(':')[1] == cond.text.partition('=')[2]:
                                                cost += (y+1)
                                                break
                                else:
                                    # There were no extra conditions -> check value of cost
                                    found = True
                                    for y, pref_val in enumerate(cond_pref.findall('PREFERENCE')):
                                        if ':' not in pref_val.text:
                                            break
                                        if pref_val.text.split(':')[1] == cond.text.partition('=')[2]:
                                            cost += (y+1)
                                            break
                            if found:
                                break

                # Form preferences-line and determine + add cost
                for pref_val in pref_stat.findall('CONDITION'):
                    specobj[pref_val.text.split('_')[1].split('=')[0]] = pref_val.text.split('_')[1].split('=')[1]
                for pref_val in pref_stat.findall('PREFERENCE'):
                    specobj[pref_stat[1].text.partition('_')[2]] = pref_val.text.partition(':')[0]
                    # Add calculated cost
                    specobj['Order'] = str(cost)
                    missing_voc_term_list = []
                    preferLine = ""
                    # Check for missing vocabulary types
                    for voc_term in voc_list:
                        if voc_term not in specobj:
                            missing_voc_term_list.append(voc_term)
                    # If there are missing items, loop over missing specs
                    if len(missing_voc_term_list) > 0:
                        fillspecs(missing_voc_term_list, 0, preferLine)
                    else:
                        for voc_item in voc_list:
                            o_idp.write(specobj[voc_item] + ', ')
                            preferLine += (specobj[voc_item] + ', ')
                        o_idp.write(specobj['Order'] + '; ')
                        preferLine = preferLine.rstrip(', ') + '; '
                        preferList.append(preferLine)
            o_idp.write('}\n    PreferList = {')
            for preferLine in preferList:
                o_idp.write(preferLine)
            o_idp.write('}\n'+line)
            flag = False
i_idp.close()

# Copy and add to theory
i_idp = open(sys.argv[1], 'r')
flag = False
for line in i_idp:
    if ("theory" in line) or flag:
        flag = True
        # Save theory name
        if 'theory' in line:
            th_name = line.split(':')
            th_name = th_name[0].lstrip()
            th_name = th_name[7:]
        if "}" not in line:
            o_idp.write(line)
        else:
            o_idp.write('{\n    ')
            for voc_item in voc_list:
                o_idp.write('!' + voc_item[0] + voc_item[-1] + '[' + voc_item + ']: ')
            o_idp.write('!Or[Order]: PreferFull(')
            for voc_item in voc_list:
                o_idp.write(voc_item[0] + voc_item[-1] + ', ')
            o_idp.write('Or) <- Prefer(')
            for voc_item in voc_list:
                o_idp.write(voc_item[0] + voc_item[-1] + ', ')
            o_idp.write('Or).\n    ')
            for voc_item in voc_list:
                o_idp.write('!' + voc_item[0] + voc_item[-1] + '[' + voc_item + ']: ')
            o_idp.write('PreferFull(')
            for voc_item in voc_list:
                o_idp.write(voc_item[0] + voc_item[-1] + ', ')
            o_idp.write('max{')
            for voc_item in voc_list:
                if voc_item not in costlist:
                    o_idp.write(voc_item[0] + voc_item[-1] + '2[' + voc_item + '], ')
            o_idp.write('Or[Order]: Prefer(')
            for voc_item in voc_list:
                if voc_item not in costlist:
                    o_idp.write(voc_item[0] + voc_item[-1] + '2, ')
                else:
                    o_idp.write(voc_item[0] + voc_item[-1]+ ', ')
            o_idp.write('Or): Or}+1) <- ~PreferList(')
            for i, voc_item in enumerate(voc_list):
                o_idp.write(voc_item[0] + voc_item[-1])
                if i+1 < len(voc_list):
                    o_idp.write(', ')
            o_idp.write(').\n}\n{\n    ')
            for voc_item in voc_list:
                o_idp.write('!' + voc_item[0] + voc_item[-1] + '[' + voc_item + ']: ')
            o_idp.write('!Or[Order]: PreferCost(')
            for voc_item in costlist:
                voc_item.rstrip(', ')
                o_idp.write(voc_item[0] + voc_item[-1] + ', ')
            o_idp.write('Or*' + basecost + ') <- PreferFull(')
            for voc_item in voc_list:
                o_idp.write(voc_item[0] + voc_item[-1] + ', ')
            o_idp.write('Or) & ' + fname + '(')
            # Get order of types in function
            fname_list = fullfname.split(',')
            fname_final_list = []
            for fname_elem in fname_list:
                elem_list = fname_elem.split(':')
                for elem in elem_list:
                    elem = elem.lstrip().rstrip(')')
                    if fname in elem:
                        elem = elem[len(fname)+1:]
                    fname_final_list.append(elem.strip('\n'))
            for i, fname_elem in enumerate(fname_final_list):
                if i+1 < len(fname_final_list):
                    o_idp.write(fname_elem[0] + fname_elem[-1])
                else:
                    o_idp.write(') = ' + fname_elem[0] + fname_elem[-1] + '.\n}\n')
                if i+2 < len(fname_final_list):
                    o_idp.write(', ')

            o_idp.write('}\n')
            flag = False
# Add term to IDP output-file
o_idp.write('term optimisation: ' + voc_name + ' {\n     sum{')
for cost_item in costlist:
    o_idp.write(cost_item[0] + cost_item[-1] + ', ')
o_idp.write('Ct: PreferCost(')
for cost_item in costlist:
    o_idp.write(cost_item[0] + cost_item[-1] + ', ')
o_idp.write('Ct): Ct}\n}\n')

# Add main() procedure for optimisation
o_idp.write('procedure main() {\n     printmodels(minimize(' + th_name + ', ' + str_name + ', optimisation))\n}')

# Close files
i_idp.close()
o_idp.close()
