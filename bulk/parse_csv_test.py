'''
Copyright (c) 2019-2020 Cisco and/or its affiliates.
 
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.0 (the "License"). A copy of the License
can be found in the LICENSE.TXT file of this software or at
                 
https://developer.cisco.com/site/licenses/CISCO-SAMPLE-CODE-LICENSE-V1.0
 
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
express or implied.


Created on Dec 18, 2019
updated
'''
import parse_csv
import unittest

class TestParseMethods(unittest.TestCase):
    
    def test_set_value_at_list_index(self):
        # set_value_at_list_index(my_list, index, value)
        my_list = list()
        parse_csv.set_value_at_list_index(my_list, [5], 10)
        answer_list = [None, None, None, None, None, 10]
        self.assertEqual(my_list, answer_list)
        
        #Take pre-existing list and append 20 on the end
        parse_csv.set_value_at_list_index(my_list, [6], 20)
        answer_list.append(20)
        self.assertEqual(my_list, answer_list)
        
        my_list = list()
        # simulate array [1][2][5] = 10
        parse_csv.set_value_at_list_index(my_list, [1,2,5], 20)
        answer_list = [None, [None, None, [None, None, None, None, None, 20]]]
        self.assertEqual(my_list, answer_list)
        
        parse_csv.set_value_at_list_index(my_list, [1,2,4], 50)
        answer_list = [None, [None, None, [None, None, None, None, 50, 20]]]
        self.assertEqual(my_list, answer_list)
        
        parse_csv.set_value_at_list_index(my_list, [2,2,4], 100)
        answer_list = [None, [None, None, [None, None, None, None, 50, 20]], [None, None,[None, None, None, None, 100]]]
        self.assertEqual(my_list, answer_list)
        
    def test_update_list_in_dict(self):
        #update_list_in_dict(dict_to_set, variable, index, variable_value)
        my_dict = {}
        parse_csv.update_list_in_dict(my_dict, 'variable', [3], 10)
        answer_dict = {}
        answer_dict['variable'] = [None, None, None, 10]
        self.assertDictEqual(my_dict, answer_dict)    
        parse_csv.update_list_in_dict(my_dict, 'variable', [7], 20)
        answer_dict['variable'] = [None, None, None, 10, None, None, None, 20]
        self.assertDictEqual(my_dict, answer_dict)    
        parse_csv.update_list_in_dict(my_dict, 'variablea', [2], 50)
        answer_dict['variablea'] = [None, None, 50]
        self.assertDictEqual(my_dict, answer_dict)
        my_dict = {}    
        parse_csv.update_list_in_dict(my_dict, 'variable', [3,1,0], 10)
        answer_dict = {'variable': [None, None, None, [None, [10]]]}
        self.assertDictEqual(my_dict, answer_dict)
        
          
    def test_set_variable_in_dict(self):
        #set_variable_in_dict(dict_to_set, variable_name, variable_value)
        my_dict = {}
        parse_csv.set_variable_in_dict(my_dict, 'variable', 10)
        parse_csv.set_variable_in_dict(my_dict, 'variable1', 20)
        parse_csv.set_variable_in_dict(my_dict, 'variablea[0]', 30)
        parse_csv.set_variable_in_dict(my_dict, 'variablea[1]', 40)
        parse_csv.set_variable_in_dict(my_dict, 'variableb[0].cat', 'cat')
        parse_csv.set_variable_in_dict(my_dict, 'variableb[0].dog', 'dog')
        parse_csv.set_variable_in_dict(my_dict, 'variableb[1].dog', 'mutt')
        parse_csv.set_variable_in_dict(my_dict, 'variableb[1].cat', 'meow')
        parse_csv.set_variable_in_dict(my_dict, 'variableb[1].chicken.feather', 'red')
        answer_dict = {}
        answer_dict['variable'] = 10
        answer_dict['variable1'] = 20
        answer_dict['variablea'] = [30, 40]
        answer_dict['variableb'] = [{'cat':'cat', 'dog':'dog'}, {'dog':'mutt', 'cat': 'meow', 'chicken':{'feather':'red'}}]
        self.assertDictEqual(my_dict, answer_dict)  
    
    def test_parse_csv_to_dict(self):
        #parse_csv_to_dict(csv_file)
        parsed_list = parse_csv.parse_csv_to_dict('./sample_network_object.csv')
        answer_list = [{'name':'host1', 
                        'description':'description1', 
                        'subType':'HOST', 
                        'value': '1.1.1.1', 
                        'type':'networkObject'}, 
                       {
                        'name':'host2', 
                        'description':'description 2', 
                        'subType':'HOST', 
                        'value': '2.2.2.2', 
                        'type':'networkObject'}
                      ]
        self.assertEqual(parsed_list, answer_list)

    def test_parse_csv_to_dict2(self):
        #my_num(int), my_num_2.nested, val[0], val[1], vala[0].dog, valb[0][1].chicken
        #1, 45, horse, pig, cocker spaniel, rooster
        #5, 20, goat, rat, cockapoo, rooster
        parsed_list = parse_csv.parse_csv_to_dict('./test_basic.csv')
        answer_list = [{'my_num':1, 'my_num_2':{'nested':'45'}, 'val':['horse', 'pig'], 'vala':[{'dog': 'cocker spaniel'}], 'valb':[[None, {'chicken':'rooster'}]]}, 
                       {'my_num':5, 'my_num_2':{'nested':'20'}, 'val':['goat', 'rat'], 'vala':[{'dog': 'cockapoo'}], 'valb':[[None, {'chicken':'rooster'}]]}
                      ]
        self.assertEqual(parsed_list, answer_list)
        
    def test_parse_csv_to_dict_with_numeric(self):
        parsed_list = parse_csv.parse_csv_to_dict('./test_numeric.csv')
        self.assertTrue(type(parsed_list[0]['number']) == int)
        self.assertTrue(type(parsed_list[0]['string']) == str)
        self.assertTrue(type(parsed_list[1]['number']) == int)
        self.assertTrue(type(parsed_list[1]['string']) == str)
        self.assertTrue(type(parsed_list[2]['number']) == int)
        self.assertTrue(type(parsed_list[2]['string']) == str)
        
        


if __name__ == '__main__':
    unittest.main()