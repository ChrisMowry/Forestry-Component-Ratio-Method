import math, sqlite3, numbers, os

class Component_Ratio_Method(object):

    def __init__(self):
        self.WATER_WEIGHT = 62.4 # lbs of ft^3 of water

        # uses the coefficients SQLite DB to get various species coefficients 
        self.current_dir = os.path.dirname(__file__)
        self.db = os.path.join(self.current_dir, 'coefficients.db')
        try:
            self.connect = sqlite3.connect(self.db)
        except:
            raise ReferenceError('Cant connect to coefficients sqlite database.')

    
    def close(self):
        self.connect.close()


    def _dataSerializer(self, cursor, row):
        data = {}
        for idx, col in enumerate(cursor.description):
            data[col[0]] = row[idx]
        return data


    def _isNumber(self, variableName, number):
        if not isinstance(number, numbers.Number):
            raise Exception('{0} must be a number.'.format(variableName))   


    def _isPositiveNumber(self, variableName, number):
        if not isinstance(number, numbers.Number):
            raise Exception('{0} must be a number.'.format(variableName))
        if number < 0:
            raise Exception('{0} must be > 0.'.format(variableName))


    def _getSpeciesData(self, species_cd):

        # # checks for proper data types
        if not type(species_cd) == int:
            raise Exception('Species code must be an integer.')

        sqlString = 'SELECT * FROM species WHERE species_cd = {0}'.format(species_cd)

        self.connect.row_factory = self._dataSerializer
        cursor = self.connect.cursor()
        cursor.execute(sqlString)
        species_data = cursor.fetchone()
        cursor.close()

        if species_data == None:
            raise Exception('Species not found in database.')

        return species_data

    def _getConfigSpeciesCode(self, species_cd, region_id):
        # TODO implement this code here
        return 0


    def _calcTotalAGBioMassJenkins(self, species, dbh):

        # checks for proper data types
        self._isPositiveNumber('DBH', dbh)
        self._isNumber('Jenkins Total B1', species['jenkins_total_b1'])
        self._isNumber('Jenkins Total B2', species['jenkins_total_b2'])

        result =  math.exp( 
                    species['jenkins_total_b1'] + 
                    species['jenkins_total_b2'] * 
                    math.log(dbh * 2.54))

        result *= 2.2046

        return result


    def _calcStemRatio(self, species, dbh):

        # checks for proper data types
        self._isPositiveNumber('DBH', dbh)
        self._isNumber('Jenkins Stem Wood B1', species['jenkins_stem_wood_ratio_b1'])
        self._isNumber('Jenkins Stem Wood B2', species['jenkins_stem_wood_ratio_b2'])
        
        result =  math.exp( 
                    species['jenkins_stem_wood_ratio_b1'] + 
                    species['jenkins_stem_wood_ratio_b2'] / 
                    (dbh * 2.54))

        return result


    def _calcBarkRatio(self, species, dbh):

        # checks for proper data types
        self._isPositiveNumber('DBH', dbh)
        self._isNumber('Jenkins Stem Bark B1', species['jenkins_stem_bark_ratio_b1'])
        self._isNumber('Jenkins Stem Bark B2', species['jenkins_stem_bark_ratio_b2'])
        
        result =  math.exp( 
                    species['jenkins_stem_bark_ratio_b1'] + 
                    species['jenkins_stem_bark_ratio_b2'] / 
                    (dbh * 2.54))

        return result


    def _calcFoliageRatio(self, species, dbh):

        # checks for proper data types
        self._isPositiveNumber('DBH', dbh)
        self._isNumber('Jenkins Foliage Ratio B1', species['jenkins_foliage_ratio_b1'])
        self._isNumber('Jenkins Foliage Ratio B2', species['jenkins_foliage_ratio_b2'])
        
        result =  math.exp( 
                    species['jenkins_foliage_ratio_b1'] + 
                    species['jenkins_foliage_ratio_b2'] / 
                    (dbh * 2.54))

        return result


    def _calcRootRatio(self, species, dbh):

        # checks for proper data types
        self._isPositiveNumber('DBH', dbh)
        self._isNumber('Jenkins Foliage Ratio B1', species['jenkins_root_ratio_b1'])
        self._isNumber('Jenkins Foliage Ratio B2', species['jenkins_root_ratio_b2'])

        result =  math.exp( 
                    species['jenkins_root_ratio_b1'] + 
                    species['jenkins_root_ratio_b2'] / 
                    (dbh * 2.54))

        return result


    def _calcStemBiomassJenkinsLbs(self, species, dbh):
        return self._calcTotalAGBioMassJenkins(species, dbh) * self._calcStemRatio(species, dbh)


    def _calcBarkBiomassJenkinsLbs(self, species, dbh):
        return self._calcTotalAGBioMassJenkins(species, dbh) * self._calcBarkRatio(species, dbh)


    def _calcBoleBiomassJenkinsLbs(self, species, dbh):
        return self._calcStemBiomassJenkinsLbs(species, dbh) + self._calcBarkBiomassJenkinsLbs(species, dbh)


    def _calcFoliageBiomassJenkinsLbs(self, species, dbh):
        return self._calcTotalAGBioMassJenkins(species, dbh) * self._calcFoliageRatio(species, dbh)


    def _calcRootBiomassJenkinsLbs(self, species, dbh):
        return self._calcTotalAGBioMassJenkins(species, dbh) * self._calcRootRatio(species, dbh)


    def _stumpVolumeEquation(self, a, b, height):
        value =  math.pow((a - b), 2) * height
        value += (11 * b)*(a - b) * math.log( height + 1)
        value -= (30.25 / (height + 1 )) * math.pow(b,2)

        return value


    def _calcStumpVolumeOutsideBark(self, species, dbh):

        # checks for proper data types
        self._isPositiveNumber('DBH', dbh)
        self._isNumber('Raile Stump DOB B1', species['raile_stump_dob_b1'])

        scaler = ( math.pi * ( math.pow( dbh ,2 ) )) / 576.0
        upperLimit = self._stumpVolumeEquation( 1.0, species['raile_stump_dob_b1'], 1.0)
        lowerLimit = self._stumpVolumeEquation( 1.0, species['raile_stump_dob_b1'], 0.0)

        return scaler * ( upperLimit - lowerLimit )

    
    def _calcStumpVolumeInsideBark(self, species, dbh):

        # checks for proper data types
        self._isPositiveNumber('DBH', dbh)
        self._isNumber('Raile Stump DIB B1', species['raile_stump_dib_b1'])
        self._isNumber('Raile Stump DIB B2', species['raile_stump_dib_b2'])

        scaler = ( math.pi * ( math.pow( dbh ,2 ) )) / 576.0
        upperLimit = self._stumpVolumeEquation( species['raile_stump_dib_b1'], species['raile_stump_dib_b2'], 1.0)
        lowerLimit = self._stumpVolumeEquation( species['raile_stump_dib_b1'], species['raile_stump_dib_b2'], 0.0)

        return scaler * ( upperLimit - lowerLimit )


    def _calcComponentRatioAdjustmentFactor(self):
        # TODO implement this method
        return 0


    def _calcStumpBiomassLbs(self, species, dbh):

        woodSPGravity = species['wood_spgr_greenvol_drywt']
        barkSPGravity = species['bark_spgr_greenvol_drywt']
        volInsideBark = self._calcStumpVolumeInsideBark(species, dbh)
        volOutsideBark = self._calcStumpVolumeOutsideBark(species, dbh)
        stumpWoodBioMass = volInsideBark * woodSPGravity * self.WATER_WEIGHT
        stumpBarkBioMass = (volOutsideBark - volInsideBark) * barkSPGravity * self.WATER_WEIGHT

        # TODO add parameters to _calcComponentRatioAdjustmentFactor 
        return ( stumpWoodBioMass + stumpBarkBioMass ) * self._calcComponentRatioAdjustmentFactor()


    def _calcTopBiomassJenkinsLbs(self, species, dbh, height):
        return (self._calcTotalAGBioMassJenkins(species, dbh)  - 
                self._calcStemBiomassJenkinsLbs(species, dbh)  - 
                self._calcBarkBiomassJenkinsLbs(species, dbh)  -
                self._calcFoliageBiomassJenkinsLbs(species, dbh) - 
                self._calcStumpBiomassLbs(species, dbh, height))


    def getVOLCFGRS(self, species, region_id, x1, x2, x3):

        volcfgrs = None
        adjSpeciesId = self._getConfigSpeciesCode(species['species_cd'], region_id )

        # TODO change species['species_cd'] to adjSpeciesId

        # Northeastern States (CT,DE,ME,MD,MA,NH,NJ,NY,OH,PA,RI,VT,WV) Table 1
        # Table 1 Row 5
        if region_id == 'S24':

            # TODO implement the calculation here
            print('Table 1 Row 5')

            volcfgrs

        # Southern States (AL,AR,FL,GA,KY,LA,MS,NC,OK,SC,TN,TX,VA) Table 2
        elif region_id == 'S33':

            # Table 2 Row 1
            if adjSpeciesId not in [58, 59, 69, 106, 140, 
                                    141, 61, 63, 66, 303,
                                    321, 755, 756, 758, 810,
                                    843, 846, 867, 8513, 122, 202]:

                # TODO implement the calculation here
                print('Table 2 Row 1')

            # Table 2 Row 2
            elif adjSpeciesId in [58, 59, 69, 106, 140, 141]:

                # TODO implement the calculation here
                print('Table 2 Row 2')

            # Table 2 Row 3
            elif species['species_cd'] in [61, 63, 66, 303, 321,
                                           755, 756, 758, 810, 843, 
                                           846, 867, 8513]:

                # TODO implement the calculation here
                print('Table 2 Row 3')

            # Table 2 Row 4
            elif species['species_cd'] == 122:

                # TODO implement the calculation here
                print('Table 2 Row 4')

            # Table 2 Row 5
            elif species['species_cd'] == 202:

                # TODO implement the calculation here
                print('Table 2 Row 5')

            else:
                raise Exception("Unknown equation for region and species!")

        # Central States (IL,IN,IA,MO), Lake States (MI,MN,WI), & Plains States (KS,NE,ND,SD) Table 1
        elif region_id in ['S23LCS',  'S23LLS', 'S23LPS']:
            
            # Table 1 Row 1
            if (( region_id in ['S23LCS', 'S23LPS'] and species['species_cd'] not in [66, 122] ) 
                    or ( region_id == 'S23LCS' and species['species_cd'] == 122 ) ):

                # TODO implement the calculation here
                print('Table 1 Row 1')

            # Table 1 Row 2
            elif region_id == 'S23LLS' and species['species_cd'] != 66:
                # TODO implement the calculation here
                print('Table 1 Row 2')

            # Table 1 Row 4
            elif region_id == 'S23LPS' and species['species_cd'] == 122:
                # TODO implement the calculation here
                print('Table 1 Row 4')

            # Table 1 Row 3
            elif species['species_cd'] == 66:
                # TODO implement the calculation here
                print('Table 1 Row 3')
            else:
                raise Exception("Unknown equation for region and species!")

        # Rocky Mountain States (AZ, CO, ID, MT, NM, NV, UT, WY) Table 3
        elif region_id in ['S22LAZN', 'S22LAZS', 
                           'S22LCOE', 'S22LCOW',
                           'S22LID',
                           'S22LMTE', 'S22LMTW',
                           'S22LNMN', 'S22LNMS', 
                           'S22LNV',
                           'S22LUTNE', 'S22LUTSW',
                           'S22LWYE', 'S22LWYW']:

            # Table 3 Row 1
            if ((( region_id in ['S22LAZN', 'S22LAZS', 'S22LNMN', 'S22LNMS', 'S22LUTSW'] )
                   and ( species['species_cd'] in [15, 17, 18, 19, 20, 
                                               21, 22, 93, 94, 96, 
                                               101, 102, 104, 108, 113, 
                                               114, 142, 202, 351, 352, 
                                               353, 374, 375, 746] )) 
                  or ( species['species_cd'] == 103 )) :

                # TODO implement the calculation here
                print('Table 3 Row 1')

            # Table 3 Row 2
            elif ((( region_id in ['S22LCOE', 'S22LCOW', 'S22LNV', 'S22LUTNE', 'S22LWYE', 'S22LWYW'] )
                     and ( species['species_cd'] in [15, 17, 18, 19, 20, 
                                                     21, 22, 93, 94, 96, 
                                                     101, 102, 104, 108, 113, 
                                                     114, 142, 202, 351, 352, 
                                                     353, 374, 375, 746] ))

                    or (( region_id in ['S22LCOE', 'S22LMTE', 'S22LWYE'])
                          and (species['species_cd'] in [51, 112, 116, 118, 122, 135, 137, 231]))
                          
                    or ((region_id in ['S22LCOE', 'S22LCOW', 'S22LNV','S22LWYE', 'S22LWYW'])
                         and (species['species_cd'] == 104 ))):

                # TODO implement the calculation here
                print('Table 3 Row 2')

            # Table 3 Row 3
            elif ((( region_id in ['S22LID', 'S22LMTE', 'S22LMTW'] )
                     and ( species['species_cd'] in [15, 17, 20, 21, 22, 
                                                     72, 73, 101, 102, 104, 
                                                     108, 113, 114, 142, 202] ))
                                                     
                    or (( region_id in ['S22LID', 'S22LMTW'])
                          and ( species['species_cd'] in [51, 112, 116, 118, 122, 
                                                          135, 137, 231] ))
                    
                    or (( region_id in ['S22LAZS', 'S22LCOW','S22LID',
                                        'S22LMTE', 'S22LMTW', 'S22LNMS',
                                        'S22LNV', 'S22LWYW'] )
                          and ( species['species_cd'] in [117, 119] ))):

                # TODO implement the calculation here
                print('Table 3 Row 3')
            
            # Table 3 Row 4
            elif (((region_id in ['S22LID', 'S22LMTE', 'S22LMTW'] )
                     and ( species['species_cd'] in [18, 19, 81, 93, 94, 
                                                     96, 351, 352, 353, 374, 
                                                     375, 746] ))
                                                     
                    or (( region_id in ['S22LAZS', 'S22LCOE', 'S22LCOW',
                                        'S22LID', 'S22LMTE', 'S22LMTW',
                                        'S22LNMS', 'S22LUTNE', 'S22LUTSW',
                                        'S22LWYE', 'S22LWYW'])
                          and ( species['species_cd'] in [242, 263, 264] ))

                    or ( species['species_cd'] in [741, 742, 745, 747, 748, 749] )):

                # TODO implement the calculation here
                print('Table 3 Row 4')

            # Table 3 Row 5
            elif (((region_id in ['S22LAZN', 'S22LAZS', 'S22LNMN', 'S22LNMS', 'S22LUTSW'])
                     and ( species['species_cd'] in [51, 112, 116, 118, 122, 135, 137, 231] ))):
                
                # TODO implement the calculation here
                print('Table 3 Row 5')

            # Table 3 Row 6
            elif (((region_id in ['S22LCOW', 'S22LNV', 'S22LUTNE', 'S22LWYW'])
                     and ( species['species_cd'] in [51, 112, 116, 118, 122, 135, 137, 231] ))):
                
                # TODO implement the calculation here
                print('Table 3 Row 6')

            # Table 3 Row 8
            elif (((region_id in ['S22LID', 'S22LMTE', 'S22LMTW', 'S22LNV'])
                     and ( species['species_cd'] == 64 ))):
                
                # TODO implement the calculation here
                print('Table 3 Row 8')

            # Table 3 Row 11
            elif (((region_id in ['S22LAZN', 'S22LAZS', 'S22LNMN', 'S22LNMS'] )
                     and ( species['species_cd'] in [322, 814] ))

                     or ( species['species_cd'] in [756, 757, 758, 803, 810,
                                                    829, 843, 846, 847] )):
                
                # TODO implement the calculation here
                print('Table 3 Row 11')

            # Table 3 Row 12
            elif ((region_id in ['S22LCOE', 'S22LCOW', 'S22LID', 'S22LMTE', 'S22LMTW',
                                  'S22LNV', 'S22LUTNE', 'S22LUTSW','S22LWYE', 'S22LWYW'])
                     and ( species['species_cd'] in [322, 814] )):
                
                # TODO implement the calculation here
                print('Table 3 Row 12')

            # Table 3 Row 7
            elif species['species_cd'] in [58, 59, 62, 63, 65, 
                                           66, 69, 106, 134, 140, 143]:
                
                # TODO implement the calculation here
                print('Table 3 Row 7')
            
            # Table 3 Row 9
            elif species['species_cd'] in [68, 130, 136, 313, 361, 
                                           362, 404, 461, 462, 492, 
                                           544, 547, 552, 602, 606, 
                                           732, 823, 826, 901, 972, 974]:
                
                # TODO implement the calculation here
                print('Table 3 Row 9')

            # Table 3 Row 10
            elif species['species_cd'] in [133, 475]:
                
                # TODO implement the calculation here
                print('Table 3 Row 10')

            else:
                raise Exception("Unknown equation for region and species!")

        # Pacific Northwest (AK, CA, OR, WA) Table 4
        elif region_id in ['S26LCA', 'S26LCAMIX', 
                           'S26LEOR', 'S26LWOR', 'S26LORJJ',
                           'S26LEWA', 'S26LWWA', 'S26LWACF',
                           'S27LAK', 'S27LAK1AB', 'S27LAK1C', 'S27LAK2A', 'S27LAK2B',
                           'S27LAK2C', 'S27LAK3A', 'S27LAK3B', 'S27LAK3C', 'S27LAK3D',
                           'S27LAK3E', 'S27LAK3F']:

            # Table 4 Row 1
            if ((( region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LWOR', 
                                 'S26LORJJ','S26LEWA', 'S26LWWA', 'S26LWACF'] )
                   and ( species['species_cd'] in [11, 42, 93, 98, 231, 242, 352])) 

                or (( region_id in ['S26LEOR', 'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( species['species_cd'] == 15 ))

                or (( region_id in ['S26LEOR', 'S26LWOR', 'S26LORJJ', 'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( species['species_cd'] in [17, 19, 22, 73, 101, 108, 119] ))
                  
                or (( region_id == 'S26LEOR')
                      and ( species['species_cd'] == 20 ))

                or (( region_id in ['S26LCA', 'S26LCAMIX'])
                      and ( species['species_cd'] in [41, 251, 746, 747, 748, 760, 766, 768] ))

                or (( region_id in ['S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( species['species_cd'] == 72 ))                

                or (( region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LWOR', 'S26LORJJ', 'S26LEWA'])
                      and ( species['species_cd'] == 92 )) 

                or (( region_id in ['S26LEOR', 'S26LWOR', 'S26LORJJ', 'S26LWWA'])
                      and ( species['species_cd'] == 103 )) 

                or (( region_id in ['S26LWOR', 'S26LORJJ'])
                      and ( species['species_cd'] in [113, 130] )) 

                or (( region_id in ['S26LEOR', 'S26LWOR'])
                      and ( species['species_cd'] == 341 ))

                or (( region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LORJJ','S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( species['species_cd'] == 351 )) 

                or (( region_id == 'S26LCA')
                      and ( species['species_cd'] == 611))):

                # TODO implement the calculation here
                print('Table 4 Row 1')

            # Table 4 Row 2
            elif ((( region_id in ['S26LCA', 'S26LCAMIX'] )
                   and ( species['species_cd'] in [14, 19, 22])) 

                or (( region_id in ['S26LCA', 'S26LCAMIX','S26LWOR', 'S26LORJJ'])
                      and ( species['species_cd'] == 20))

                or (( region_id in ['S26LCA', 'S26LCAMIX','S26LEOR', 'S26LWOR', 'S26LORJJ'])
                      and ( species['species_cd'] == 21))):

                # TODO implement the calculation here
                print('Table 4 Row 2')

            # Table 4 Row 3
            elif ((( region_id in ['S26LCA', 'S26LCAMIX','S26LWOR', 'S26LORJJ'] )
                   and ( species['species_cd'] == 15)) 

                or (( region_id in ['S26LCA', 'S26LCAMIX'])
                      and ( species['species_cd'] == 17))):

                # TODO implement the calculation here
                print('Table 4 Row 3')

            # Table 4 Row 4
            elif ((( region_id in ['S26LEOR', 'S26LWOR', 'S26LORJJ', 'S26LEWA', 'S26LWWA', 'S26LWACF'] )
                   and ( species['species_cd'] == 41)) 

                or (( region_id in ['S26LCA', 'S26LCAMIX'])
                      and ( species['species_cd'] in [50, 51, 54, 55]))

                or (( region_id == 'S26LCA')
                      and ( species['species_cd'] in [52, 53]))                     
                      
                or (( region_id in ['S26LCA', 'S26LCAMIX', 
                                    'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                    'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( species['species_cd'] == 81))):

                # TODO implement the calculation here
                print('Table 4 Row 4')

            # Table 4 Row 5
            elif ((( region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LWOR', 'S26LORJJ'] )
                   and ( species['species_cd'] in [62, 65, 66]))                   
                      
                or (( region_id in ['S26LCA', 'S26LCAMIX', 
                                    'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                    'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( species['species_cd'] in [133, 321, 475]))):

                # TODO implement the calculation here
                print('Table 4 Row 5')

            # Table 4 Row 6
            elif ((( region_id in ['S26LCA', 'S26LCAMIX', 
                                    'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                    'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( species['species_cd'] == 64))):

                # TODO implement the calculation here
                print('Table 4 Row 6')

            # Table 4 Row 7
            elif ((( region_id in ['S26LCA', 'S26LCAMIX'] )
                   and ( species['species_cd'] in [102, 103, 104, 108, 113, 124, 142]))                   
                      
                or (( region_id in ['S26LCA', 'S26LCAMIX', 
                                    'S26LEOR', 'S26LWOR', 'S26LORJJ'])
                      and ( species['species_cd'] == 120))):

                # TODO implement the calculation here
                print('Table 4 Row 7')

            # Table 4 Row 8
            elif ((( region_id in ['S26LCA', 'S26LCAMIX'] )
                   and ( species['species_cd'] in [101, 109, 119, 127, 137]))                   
                      
                or (( region_id in ['S26LCA', 'S26LCAMIX', 'S26LWOR', 'S26LORJJ'])
                      and ( species['species_cd'] in [116, 122]))

                or (( region_id in ['S26LCA', 'S26LCAMIX', 
                                    'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                    'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( species['species_cd'] == 117))):

                # TODO implement the calculation here
                print('Table 4 Row 8')

            # Table 4 Row 9
            elif ((( region_id == 'S26LEOR' )
                   and ( species['species_cd'] == 116))                   
                      
                or (( region_id in ['S26LEOR', 'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( species['species_cd'] == 122))

                or (( region_id in ['S26LEOR', 'S26LEWA'])
                      and ( species['species_cd'] == 202))):

                # TODO implement the calculation here
                print('Table 4 Row 9')

            # Table 4 Row 10
            elif (( region_id in ['S26LCA', 'S26LCAMIX']  )
                   and ( species['species_cd'] in [201, 202])):

                # TODO implement the calculation here
                print('Table 4 Row 10')

             # Table 4 Row 11
            elif (( region_id in ['S26LWOR', 'S26LORJJ', 'S26LWWA', 'S26LWACF']  )
                   and ( species['species_cd'] == 202)):

                # TODO implement the calculation here
                print('Table 4 Row 11')

             # Table 4 Row 12
            elif (( region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LWOR', 'S26LORJJ']  )
                   and ( species['species_cd'] in [211, 212])):

                # TODO implement the calculation here
                print('Table 4 Row 12')

            # Table 4 Row 13
            elif (( region_id in ['S26LCA', 'S26LCAMIX', 
                                  'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                  'S26LEWA', 'S26LWWA', 'S26LWACF'])
                   and ( species['species_cd'] == 263)):

                # TODO implement the calculation here
                print('Table 4 Row 13')

            # Table 4 Row 14
            elif (( region_id in ['S26LCA', 'S26LCAMIX', 
                                  'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                  'S26LEWA', 'S26LWWA', 'S26LWACF'])
                   and ( species['species_cd'] in [264, 299])):

                # TODO implement the calculation here
                print('Table 4 Row 14')   

            # Table 4 Row 15
            elif (( region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LWOR', 'S26LORJJ'])
                   and ( species['species_cd'] in [312, 313, 361, 431, 540, 
                                                   542, 815, 818, 901, 997])
                   
                or ((region_id == 'S26LWOR')
                    and species['species_cd'] == 320 )

                or ((region_id in ['S26LCA', 'S26LCAMIX'])
                    and species['species_cd'] in [330, 333, 421, 492, 500, 
                                                  600, 602, 660, 661, 730, 
                                                  763, 801, 807, 811, 826, 
                                                  839, 920, 998, 999] )

                or ((region_id in ['S26LCA', 'S26LCAMIX', 'S26LWOR', 'S26LORJJ'])
                    and species['species_cd'] in [631, 805, 981])
                    
                or ((region_id == 'S26LCA')
                    and species['species_cd'] in [547, 604, 731, 922])

                or ((region_id in ['S26LCA', 'S26LCAMIX', 'S26LWOR', 'S26LEWA'])
                    and species['species_cd'] == 603)

                or ((region_id in ['S26LCA', 'S26LCAMIX', 'S26LORJJ'])
                    and species['species_cd'] == 821)):

                # TODO implement the calculation here
                print('Table 4 Row 15')

            # Table 4 Row 16
            elif (( region_id in ['S26LEWA', 'S26LWWA', 'S26LWACF'])
                   and ( species['species_cd'] in [312, 313, 370, 431, 540,
                                                   542, 815, 901, 997])
                   
                or ((region_id == 'S26LWOR')
                    and species['species_cd'] in [351, 926] )

                or ((region_id in ['S26LWWA', 'S26LWACF'])
                    and species['species_cd'] == 361 )

                or ((region_id in ['S26LCA', 'S26LCAMIX', 
                                  'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                  'S26LEWA', 'S26LWWA', 'S26LWACF'] )
                    and species['species_cd'] in [374, 375, 591])
                    
                or ((region_id in ['S26LEOR', 'S26LWOR', 'S26LORJJ',
                                   'S26LEWA', 'S26LWWA', 'S26LWACF'] )
                    and species['species_cd'] in [492, 500, 602, 660, 661, 
                                                  730, 746, 747, 760, 763,
                                                  766, 768, 920, 998, 999])

                or ((region_id in ['S26LWOR', 'S26LORJJ'])
                    and species['species_cd'] == 510)

                or ((region_id in ['S26LEOR', 'S26LWOR', 'S26LORJJ', 'S26LWWA', 'S26LWACF'])
                    and species['species_cd'] == 600)

                or ((region_id in ['S26LEOR', 'S26LWWA', 'S26LWACF'])
                    and species['species_cd'] == 631)

                or ((region_id == 'S26LEWA')
                     and species['species_cd'] == 818)):

                # TODO implement the calculation here
                print('Table 4 Row 16')

            # Table 4 Row 17
            elif (( region_id in ['S26LCA', 'S26LCAMIX'])
                   and ( species['species_cd'] == 510)
                   
                or (region_id == 'S26LCA')
                    and species['species_cd'] == 511 ):

                # TODO implement the calculation here
                print('Table 4 Row 17')   

            # Table 4 Row 18
            elif (( region_id in ['S26LCA', 'S26LCAMIX'])
                   and ( species['species_cd'] == 756)
                   
                or ((region_id == 'S26LCA')
                    and species['species_cd'] == 758 )
                    
                or ((region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LEWA'])
                    and species['species_cd'] == 990 )                
                ):

                # TODO implement the calculation here
                print('Table 4 Row 18')

            # Table 4 Row 19
            elif ( region_id in ['S27LAK', 'S27LAK1AB', 'S27LAK1C', 'S27LAK2A', 'S27LAK2B',
                                 'S27LAK2C', 'S27LAK3A', 'S27LAK3B', 'S27LAK3C', 'S27LAK3D',
                                 'S27LAK3E', 'S27LAK3F']):
                raise Exception("Alaska is unsupported at this time.")

        else:
            raise Exception("Unknown region!")


if __name__ == '__main__':
    crm = Component_Ratio_Method()
    species = crm._getSpeciesData(58)
    crm.getVOLCFGRS(species, 'S33', 0, 0, 0)



