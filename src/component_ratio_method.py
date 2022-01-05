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


    def getVOLCFGRS(self, species, region_id, x1, x2, x3, v1, v2):

        # Northeastern States (CT,DE,ME,MD,MA,NH,NJ,NY,OH,PA,RI,VT,WV) Table 1
        # Table 1 Row 5
        if region_id == 'S24':

            # TODO implement the calculation here
            print('Table 1 Row 5')

        # Southern States (AL,AR,FL,GA,KY,LA,MS,NC,OK,SC,TN,TX,VA) Table 2
        elif region_id == 'S33':

            # Table 2 Row 1
            if species['species_cd'] not in [58, 59, 69, 106, 140, 
                                             141, 61, 63, 66, 303,
                                             321, 755, 756, 758, 810,
                                             843, 846, 867, 8513, 122, 202]:

                # TODO implement the calculation here
                print('Table 2 Row 1')

            # Table 2 Row 2
            elif species['species_cd'] in [58, 59, 69, 106, 140, 141]:

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
                           'S26LEOR', 'S26LWOR', 'S26LORJJ'
                           'S26LEWA', 'S26LWWA', 'S26LWACF',
                           'S27LAK', 'S27LAK1AB', 'S27LAK1C', 'S27LAK2A', 'S27LAK2B',
                           'S27LAK2C', 'S27LAK3A', 'S27LAK3B', 'S27LAK3C', 'S27LAK3D',
                           'S27LAK3E', 'S27LAK3F']:


            # TODO implement PNW logic here...
            print( 'table 4 ')


        else:
            raise Exception("Unknown region!")



    #def getVOLCFSND(self, region_id):


    # def _calcDRYBIO_BOLE(self):


    # def convertSoundVolumeToBiomass(self):
    #     print('convertSoundVolumeToBioMass')

    # def calcBarkBiomass(self):
    #     print('calculateBarkBioMass')

    # def calcTreeBiomass(self):
    #     print('calculateTreeBioMass')

    # def calcStumpVolume(self):
    #     print('calculateStumpVolume')
    
    # def calcTopBiomass(self):
    #     print('calculateTopBiomass')    

    # def calcAdjustmentFactor(self):
    #     print('calculateAdjustmentFactor')       

    # def applyAdjustmentFactor(self):
    #     print('applyAdjustmentFactor')


if __name__ == '__main__':
    crm = Component_Ratio_Method()
    species = crm._getSpeciesData(746)
    print(crm._calcStumpVolumeOutsideBark(species, 10.5))
    print(crm._calcStumpVolumeInsideBark(species, 10.5))



