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


    def _getGrossVolConfigSpeciesCode(self, species_cd, region_id):
        sqlString = 'SELECT gross_cf_spcd '
        sqlString += 'FROM config WHERE species_cd = {0} '.format(species_cd)
        sqlString += "AND rgn_config_id = '{0}' ".format(region_id)
        sqlString += 'ORDER BY  gross_cf_spcd'

        self.connect.row_factory = self._dataSerializer
        cursor = self.connect.cursor()
        cursor.execute(sqlString)
        species_cd_dict = cursor.fetchone()
        cursor.close()

        if species_cd_dict == None:
            raise Exception('There is no cooresponding gross volume species code for this species!')

        return species_cd_dict['gross_cf_spcd']

    def _getGrossVolCoeff(self, species_cd, region_id):
        sqlString = 'SELECT * '
        sqlString += 'FROM vw_gross_vol_coeff WHERE  species_cd = {0} '.format(species_cd)
        sqlString += "AND rgn_config_id = '{0}' ".format(region_id)
        sqlString += 'ORDER BY  gross_cf_spcd'

        self.connect.row_factory = self._dataSerializer
        cursor = self.connect.cursor()
        cursor.execute(sqlString)
        coefficients = cursor.fetchone()
        cursor.close()

        if coefficients == None:
            raise Exception('There is no cooresponding gross volume coefficients for this region and species.')

        return coefficients


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


    def getVOLCFGRS(self, species, region_id, 
                    dbh=None, 
                    height=None, 
                    basal_area=None, 
                    site_index=None,
                    stem_count=None,
                    drc=None,
                    bole_hgt=None):

        volcfgrs = None # holds the value to be returned
        adjGrossVolSpeciesId = self._getGrossVolConfigSpeciesCode(species['species_cd'], region_id )
        coefficients = self._getGrossVolCoeff(species['species_cd'], region_id)

        b0 = coefficients['b0']
        b1 = coefficients['b1']
        b2 = coefficients['b2']
        b3 = coefficients['b3']
        b4 = coefficients['b4']
        b5 = coefficients['b5']
        b6 = coefficients['b6']
        b7 = coefficients['b7']
        b8 = coefficients['b8']
        b9 = coefficients['b9']
        b10 = coefficients['b10']
        b11 = coefficients['b11']
        b12 = coefficients['b12']
        b13 = coefficients['b13']
        b14 = coefficients['b14']
        b15 = coefficients['b15']
        b16 = coefficients['b16']
        b17 = coefficients['b17']
        b18 = coefficients['b18']
        b19 = coefficients['b19']

        # Northeastern States (CT,DE,ME,MD,MA,NH,NJ,NY,OH,PA,RI,VT,WV) Table 1
        # Table 1 Row 5
        if region_id == 'S24':

            if bole_hgt != None:
                volcfgrs = b0 + b1 * math.pow(dbh, b2)
                volcfgrs += b3 * math.pow(dbh, b4) * math.pow(bole_hgt, b5)

            else:
                raise Exception('Northeast States requires bole height.')

        # Southern States (AL,AR,FL,GA,KY,LA,MS,NC,OK,SC,TN,TX,VA) Table 2
        elif region_id == 'S33':

            if height == None:
                raise Exception('Height is required for southern states.')

            # Table 2 Row 1
            if adjGrossVolSpeciesId not in [58, 59, 69, 106, 140, 
                                            141, 61, 63, 66, 303,
                                            321, 755, 756, 758, 810,
                                            843, 846, 867, 8513, 122, 202]:

                print('Table 2 Row 1')
                if dbh == None:
                    raise Exception('DBH is not provided.')

                if dbh > 5.0 and height != None:
                    volcfgrs = b0 + b1 * math.pow(dbh, 2.0) * height

            # Table 2 Row 2
            elif adjGrossVolSpeciesId in [58, 59, 69, 106, 140, 141]:

                print('Table 2 Row 2')
                if dbh == None:
                    raise Exception('Diameter at root collar is not provided.')

                v1 = math.pow(drc, 2.0) * height * 0.001
                
                volcfgrs = b0 + b1 * v1
                if v1 <= b3:
                    volcfgrs += b2 * math.pow(v1,2.0)
                else:
                    volcfgrs += b2 * ((3.0 * math.pow(b3, 2.0)) - (2.0 * math.pow(b3, 3.0)) / v1 )

                if volcfgrs <= 0.0:
                    volcfgrs = 0.1

            # Table 2 Row 3
            elif adjGrossVolSpeciesId in [61, 63, 66, 303, 321,
                                          755, 756, 758, 810, 843, 
                                          846, 867, 8513]:

                print('Table 2 Row 3')
                v1 = math.pow(drc, 2.0) * height * 0.001
                if v1 <= b6:
                    volcfgrs = b1 * b2 * v1 + b3 * math.pow(v1, 2.0)
                else:
                    volcfgrs = b4 * b2 * v1 - ( b5 / v1 )

                if volcfgrs <= 0.0:
                    volcfgrs = 0.1

            # Table 2 Row 4
            elif adjGrossVolSpeciesId == 122:

                print('Table 2 Row 4')
                if dbh < 21.0:
                    volcfgrs = b1 + b2 * math.pow(dbh, 2.0) * height
                    volcfgrs -= b3 + b4 * ((64.0 * height)/math.pow(dbh, b5)) + b6 * math.pow(dbh, 2.0)
                else:
                    volcfgrs = b7 + b8 * math.pow(dbh, 2.0 ) * height
                    volcfgrs -= b9 + b10 * ((64.0 * height)/math.pow(dbh, b11)) + b12 * math.pow(dbh, 2.0)
                
                if volcfgrs <= 0.0 and dbh >= 1.0:
                    volcfgrs = 0.1

            # Table 2 Row 5
            elif adjGrossVolSpeciesId == 202:

                print('Table 2 Row 5')
                volcfgrs = b1 + b2 * math.pow(dbh, 2.0) * height
                volcfgrs -= b3 + b4 * ((64.0 * height)/math.pow(dbh, b5)) + b6 * math.pow(dbh, 2.0)

                if volcfgrs <= 0.0 and dbh >= 1.0:
                    volcfgrs = 0.1

            else:
                raise Exception("Unknown equation for region and species!")

        # Central States (IL,IN,IA,MO), Lake States (MI,MN,WI), & Plains States (KS,NE,ND,SD) Table 1
        elif region_id in ['S23LCS',  'S23LLS', 'S23LPS']:
            
            # Table 1 Row 1
            if (( region_id in ['S23LCS', 'S23LPS'] and adjGrossVolSpeciesId not in [66, 122] ) 
                    or ( region_id == 'S23LCS' and adjGrossVolSpeciesId == 122 ) ):

                print('Table 1 Row 1')
                if dbh == None or site_index == None:
                    raise Exception('DBH and Site Index are needed.')

                volcfgrs = b1 * math.pow(site_index, b2) * (1.0 - math.pow(math.e, b3 * math.pow(dbh, b4)))

                if volcfgrs < 0.0:
                    volcfgrs = 0.0

            # Table 1 Row 2
            elif region_id == 'S23LLS' and adjGrossVolSpeciesId != 66:

                print('Table 1 Row 2')
                if dbh == None or site_index == None or basal_area == None:
                    raise Exception('DBH, Site Index, and Basal Area are needed.')

                if site_index < 20.0:
                    site_index = 20.0
                
                if site_index > 120.0:
                    site_index = 120.0

                if basal_area < 50.0:
                    basal_area = 50.0

                if basal_area > 350.0:
                    basal_area = 350.0

                v1 = 4.0 
                v2 = b13 * math.pow(1.0 - math.pow(math.e, (-1 * b14 * dbh)), b15 )
                v2 *= math.pow(site_index, b16)
                v2 *= math.pow(b17 - ( v1 / dbh ), b18) * math.pow(basal_area, b19)
                v2 += b12

                if volcfgrs < 0.0:
                    volcfgrs = 0.0

            # Table 1 Row 4
            elif region_id == 'S23LPS' and adjGrossVolSpeciesId == 122:
                print('Table 1 Row 4')
                if dbh == None or site_index == None:
                    raise Exception('DBH and Site Index are needed.')

                if math.pow(dbh, 2.0) * height <= b1:
                    volcfgrs = b2 + b3 * math.pow(dbh, 2.0) * height

                elif math.pow(dbh, 2.0) * height > b1:
                    volcfgrs = b4 + b5 * math.pow(dbh, 2.0) * height

                if volcfgrs <= 0.0:
                    volcfgrs = 0.1

            # Table 1 Row 3
            elif adjGrossVolSpeciesId == 66:

                print('Table 1 Row 3')
                if dbh == None or site_index == None:
                    raise Exception('Diameter at root collar and Site Index are needed.')

                v1 = math.pow(drc, 2.0) * height * 0.001
                volcfgrs = b0 + b1 * v1
                if v1 <= b3:
                    volcfgrs += b2 * math.pow(v1, 2.0)
                else:
                    volcfgrs += b2 * (3.0 * math.pow(b3, 2.0) - (( 2.0 * math.pow(b3, 3.0))/ v1))

                if volcfgrs <= 0.0:
                    volcfgrs = 0.1

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
                   and ( adjGrossVolSpeciesId in [15, 17, 18, 19, 20, 
                                                  21, 22, 93, 94, 96, 
                                                  101, 102, 104, 108, 113, 
                                                  114, 142, 202, 351, 352, 
                                                  353, 374, 375, 746] )) 
                  or ( adjGrossVolSpeciesId == 103 )) :

                print('Table 3 Row 1')
                if dbh == None or height == None:
                    raise Exception('DBH and height are needed.')

                volcfgrs = b1 + b2 * math.pow(dbh, 2.0) * height
                volcfgrs -= b3 + b4 * ((64.0 * height) / math.pow(dbh, b5)) + b6 * math.pow( dbh, 2.0)

                if volcfgrs <= 0 and dbh >= 1.0:
                    volcfgrs = 0.1

            # Table 3 Row 2
            elif ((( region_id in ['S22LCOE', 'S22LCOW', 'S22LNV', 'S22LUTNE', 'S22LWYE', 'S22LWYW'] )
                     and ( adjGrossVolSpeciesId in [15, 17, 18, 19, 20, 
                                                    21, 22, 93, 94, 96, 
                                                    101, 102, 104, 108, 113, 
                                                    114, 142, 202, 351, 352, 
                                                    353, 374, 375, 746] ))

                    or (( region_id in ['S22LCOE', 'S22LMTE', 'S22LWYE'])
                          and (adjGrossVolSpeciesId in [51, 112, 116, 118, 122, 135, 137, 231]))
                          
                    or ((region_id in ['S22LCOE', 'S22LCOW', 'S22LNV','S22LWYE', 'S22LWYW'])
                         and (adjGrossVolSpeciesId == 104 ))):

                print('Table 3 Row 2')
                if dbh == None or height == None:
                    raise Exception('DBH and height are needed.')

                if math.pow(dbh, 2.0) * height <= b5:
                    volcfgrs = b1 + b2 * math.pow(dbh, 2.0) * height

                elif math.pow(dbh, 2.0) * height > b5:
                    volcfgrs = b3 + b4 * math.pow(dbh, 2.0) * height

                if volcfgrs <= 0 and dbh >= 1.0:
                    volcfgrs = 0.1

            # Table 3 Row 3
            elif ((( region_id in ['S22LID', 'S22LMTE', 'S22LMTW'] )
                     and ( adjGrossVolSpeciesId in [15, 17, 20, 21, 22, 
                                                    72, 73, 101, 102, 104, 
                                                    108, 113, 114, 142, 202] ))
                                                     
                    or (( region_id in ['S22LID', 'S22LMTW'])
                          and ( adjGrossVolSpeciesId in [51, 112, 116, 118, 122, 
                                                         135, 137, 231] ))
                    
                    or (( region_id in ['S22LAZS', 'S22LCOW','S22LID',
                                        'S22LMTE', 'S22LMTW', 'S22LNMS',
                                        'S22LNV', 'S22LWYW'] )
                          and ( adjGrossVolSpeciesId in [117, 119] ))):

                print('Table 3 Row 3')
                if dbh == None or height == None:
                    raise Exception('DBH and height are needed.')

                v1 = b5 * math.pow(dbh, b6) * math.pow(height, b7)
                v2 = 4.0

                volcfgrs = v1 - (v1 * ( b1 * (math.pow(v2 / b2, b3) / math.pow(dbh, b4))))

                if volcfgrs <= 0:
                    volcfgrs = 0.1

            # Table 3 Row 4
            elif (((region_id in ['S22LID', 'S22LMTE', 'S22LMTW'] )
                     and ( adjGrossVolSpeciesId in [18, 19, 81, 93, 94, 
                                                    96, 351, 352, 353, 374, 
                                                    375, 746] ))
                                                     
                    or (( region_id in ['S22LAZS', 'S22LCOE', 'S22LCOW',
                                        'S22LID', 'S22LMTE', 'S22LMTW',
                                        'S22LNMS', 'S22LUTNE', 'S22LUTSW',
                                        'S22LWYE', 'S22LWYW'])
                          and ( adjGrossVolSpeciesId in [242, 263, 264] ))

                    or ( adjGrossVolSpeciesId in [741, 742, 745, 747, 748, 749] )):

                print('Table 3 Row 4')
                if dbh == None or height == None:
                    raise Exception('DBH and height are needed.')

                if math.pow(dbh, 2.0) * height <= b5 or (dbh < 21.0 and b5 == 0):
                    volcfgrs = b1 + b2 * math.pow(dbh, 2.0) * height
                else:
                    b3 + b4 * math.pow(dbh, 2.0) * height

                if volcfgrs <= 0:
                    volcfgrs = 0.1

            # Table 3 Row 5
            elif (((region_id in ['S22LAZN', 'S22LAZS', 'S22LNMN', 'S22LNMS', 'S22LUTSW'])
                     and ( adjGrossVolSpeciesId in [51, 112, 116, 118, 122, 135, 137, 231] ))):
                
                print('Table 3 Row 5')
                if dbh == None or height == None:
                    raise Exception('DBH and height are needed.')

                if dbh < 21.0:
                    volcfgrs = b1 + b2 * math.pow(dbh, 2.0) * height
                    volcfgrs -= b3 + b4 * ((64.0 * height) / math.pow(dbh, b5)) + b6 * math.pow(dbh, 2.0)
                else:
                    volcfgrs = b7 + b8 * math.pow(dbh, 2.0) * height
                    volcfgrs -= b9 + b10 * ((64.0 * height) / math.pow(dbh, b11)) + b12 * math.pow(dbh, 2.0)

                if volcfgrs <= 0 and dbh >= 1.0:
                    volcfgrs = 0.1                  

            # Table 3 Row 6
            elif (((region_id in ['S22LCOW', 'S22LNV', 'S22LUTNE', 'S22LWYW'])
                     and ( adjGrossVolSpeciesId in [51, 112, 116, 118, 122, 135, 137, 231] ))):
                
                print('Table 3 Row 6')
                if dbh == None or height == None:
                    raise Exception('DBH and height are needed.')

                if dbh > 5.0:
                    volcfgrs = b0 + b1 * math.pow(dbh, 2.0) * height

                if volcfgrs <= 0 and volcfgrs != None:
                    volcfgrs = 0.1                

            # Table 3 Row 8
            elif (((region_id in ['S22LID', 'S22LMTE', 'S22LMTW', 'S22LNV'])
                     and ( adjGrossVolSpeciesId == 64 ))):

                print('Table 3 Row 8')
                if dbh == None or height == None:
                    raise Exception('DBH and height are needed.')

                if dbh > 60.0:
                    dbh = 60.0
                
                v1_1 = (b9 * dbh * height) / (height + b10)
                v1_2 = height * math.pow( height / (height + b10), 2.0)
                v1 = b6 * math.pow(dbh, 2.0) * (b7 + b8 * height - v1_1 ) * v1_2

                if v1 <= 0.0:
                    v1 = 2.0
                
                volcfgrs = ((v1 + b1) / ( b2 + b3 * math.pow(math.e, b4 * dbh))) + b5

                if volcfgrs <= 0:
                    volcfgrs = 1.0

            # Table 3 Row 11
            elif (((region_id in ['S22LAZN', 'S22LAZS', 'S22LNMN', 'S22LNMS'] )
                     and ( adjGrossVolSpeciesId in [322, 814] ))

                     or ( adjGrossVolSpeciesId in [756, 757, 758, 803, 810,
                                                   829, 843, 846, 847] )):
                
                print('Table 3 Row 11')
                if drc == None or height == None:
                    raise Exception('Diameter at root collar and height are needed.')

                v1 = math.pow(drc, 2.0) * height * 0.001
                if v1 <= b6:
                    volcfgrs = b1 + b2 * v1 + b3 * math.pow(v1, 2.0)
                else:
                    volcfgrs = b4 + b2 * v1 - (b5 / v1)

                if volcfgrs <= 0:
                    volcfgrs = 0.1

            # Table 3 Row 12
            elif ((region_id in ['S22LCOE', 'S22LCOW', 'S22LID', 'S22LMTE', 'S22LMTW',
                                  'S22LNV', 'S22LUTNE', 'S22LUTSW','S22LWYE', 'S22LWYW'])
                     and ( adjGrossVolSpeciesId in [322, 814] )):
                
                print('Table 3 Row 12')
                if drc == None or height == None or stem_count == None:
                    raise Exception('Diameter at root collar, height and # of stems are needed.')

                if drc >= 3.0 and height > 0.0 and stem_count == 1:
                    volcfgrs = math.pow((b0 + b1 * math.pow(math.pow(drc, 2.0) * height, b2) + b3 ), 3.0)
                        
                elif drc >= 3.0 and height > 0.0 and stem_count != 1:
                    volcfgrs = math.pow((b0 + b1 * math.pow(math.pow(drc, 2.0) * height, b2)), 3.0)

                else:
                    volcfgrs = 0

                if volcfgrs <= 0:
                    volcfgrs = 0.1

            # Table 3 Row 7
            elif adjGrossVolSpeciesId in [58, 59, 62, 63, 65, 
                                          66, 69, 106, 134, 140, 143]:
                
                print('Table 3 Row 7')
                if drc == None or height == None:
                    raise Exception('Diameter at root collar and height are needed.')

                v1 = math.pow(drc, 2.0) * height * 0.001
                volcfgrs = b0 + b1 * v1 + b2
                if v1 <= b3:
                    volcfgrs += b2 * math.pow(v1, 2.0)
                else:
                    volcfgrs += b2 * (3.0 * math.pow(b3, 2.0) - ((2.0 * math.pow(b3, 3.0))/v1 ))

                if volcfgrs <= 0:
                    volcfgrs = 0.1

            # Table 3 Row 9
            elif adjGrossVolSpeciesId in [68, 130, 136, 313, 361, 
                                          362, 404, 461, 462, 492, 
                                          544, 547, 552, 602, 606, 
                                          732, 823, 826, 901, 972, 974]:
                
                print('Table 3 Row 9')
                if dbh == None:
                    raise Exception('DBH is needed.')

                if (adjGrossVolSpeciesId < 300 and dbh < 9.0) or (adjGrossVolSpeciesId >= 300 and dbh < 11.0):
                    volcfgrs = b1 + b2 * math.pow(dbh, 2.0) * height
                else:
                    volcfgrs = b3 + b4 * math.pow(dbh, 2.0) * height

                if volcfgrs <= 0 or height == None or dbh < 5.0:
                    volcfgrs = 0.1

            # Table 3 Row 10
            elif adjGrossVolSpeciesId in [133, 475]:
                
                print('Table 3 Row 10')
                if drc == None or height == None or stem_count == None:
                    raise Exception('Diameter at root collar, height and # of stems are needed.')

                if drc >= 3.0 and height > 0.0 and stem_count == 1:
                    volcfgrs = math.pow((b0 + b1 * math.pow(math.pow(drc, 2.0) * height, b2) + b3 ), 3.0)
                        
                elif drc >= 3.0 and height > 0.0 and stem_count != 1:
                    volcfgrs = math.pow((b0 + b1 * math.pow(math.pow(drc, 2.0) * height, b2)), 3.0)

                else:
                    volcfgrs = 0.1

                if volcfgrs <= 0:
                    volcfgrs = 0.1

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
                   and ( adjGrossVolSpeciesId in [11, 42, 93, 98, 231, 242, 352])) 

                or (( region_id in ['S26LEOR', 'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( adjGrossVolSpeciesId == 15 ))

                or (( region_id in ['S26LEOR', 'S26LWOR', 'S26LORJJ', 'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( adjGrossVolSpeciesId in [17, 19, 22, 73, 101, 108, 119] ))
                  
                or (( region_id == 'S26LEOR')
                      and ( adjGrossVolSpeciesId == 20 ))

                or (( region_id in ['S26LCA', 'S26LCAMIX'])
                      and ( adjGrossVolSpeciesId in [41, 251, 746, 747, 748, 760, 766, 768] ))

                or (( region_id in ['S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( adjGrossVolSpeciesId == 72 ))                

                or (( region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LWOR', 'S26LORJJ', 'S26LEWA'])
                      and ( adjGrossVolSpeciesId == 92 )) 

                or (( region_id in ['S26LEOR', 'S26LWOR', 'S26LORJJ', 'S26LWWA'])
                      and ( adjGrossVolSpeciesId == 103 )) 

                or (( region_id in ['S26LWOR', 'S26LORJJ'])
                      and ( adjGrossVolSpeciesId in [113, 130] )) 

                or (( region_id in ['S26LEOR', 'S26LWOR'])
                      and ( adjGrossVolSpeciesId == 341 ))

                or (( region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LORJJ','S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( adjGrossVolSpeciesId == 351 )) 

                or (( region_id == 'S26LCA')
                      and ( adjGrossVolSpeciesId == 611))):

                # TODO implement the calculation here
                print('Table 4 Row 1')

            # Table 4 Row 2
            elif ((( region_id in ['S26LCA', 'S26LCAMIX'] )
                   and ( adjGrossVolSpeciesId in [14, 19, 22])) 

                or (( region_id in ['S26LCA', 'S26LCAMIX','S26LWOR', 'S26LORJJ'])
                      and ( adjGrossVolSpeciesId == 20))

                or (( region_id in ['S26LCA', 'S26LCAMIX','S26LEOR', 'S26LWOR', 'S26LORJJ'])
                      and ( adjGrossVolSpeciesId == 21))):

                # TODO implement the calculation here
                print('Table 4 Row 2')

            # Table 4 Row 3
            elif ((( region_id in ['S26LCA', 'S26LCAMIX','S26LWOR', 'S26LORJJ'] )
                   and ( adjGrossVolSpeciesId == 15)) 

                or (( region_id in ['S26LCA', 'S26LCAMIX'])
                      and ( adjGrossVolSpeciesId == 17))):

                # TODO implement the calculation here
                print('Table 4 Row 3')

            # Table 4 Row 4
            elif ((( region_id in ['S26LEOR', 'S26LWOR', 'S26LORJJ', 'S26LEWA', 'S26LWWA', 'S26LWACF'] )
                   and ( adjGrossVolSpeciesId == 41)) 

                or (( region_id in ['S26LCA', 'S26LCAMIX'])
                      and ( adjGrossVolSpeciesId in [50, 51, 54, 55]))

                or (( region_id == 'S26LCA')
                      and ( adjGrossVolSpeciesId in [52, 53]))                     
                      
                or (( region_id in ['S26LCA', 'S26LCAMIX', 
                                    'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                    'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( adjGrossVolSpeciesId == 81))):

                # TODO implement the calculation here
                print('Table 4 Row 4')

            # Table 4 Row 5
            elif ((( region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LWOR', 'S26LORJJ'] )
                   and ( adjGrossVolSpeciesId in [62, 65, 66]))                   
                      
                or (( region_id in ['S26LCA', 'S26LCAMIX', 
                                    'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                    'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( adjGrossVolSpeciesId in [133, 321, 475]))):

                # TODO implement the calculation here
                print('Table 4 Row 5')

            # Table 4 Row 6
            elif ((( region_id in ['S26LCA', 'S26LCAMIX', 
                                    'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                    'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( adjGrossVolSpeciesId == 64))):

                # TODO implement the calculation here
                print('Table 4 Row 6')

            # Table 4 Row 7
            elif ((( region_id in ['S26LCA', 'S26LCAMIX'] )
                   and ( adjGrossVolSpeciesId in [102, 103, 104, 108, 113, 124, 142]))                   
                      
                or (( region_id in ['S26LCA', 'S26LCAMIX', 
                                    'S26LEOR', 'S26LWOR', 'S26LORJJ'])
                      and ( adjGrossVolSpeciesId == 120))):

                # TODO implement the calculation here
                print('Table 4 Row 7')

            # Table 4 Row 8
            elif ((( region_id in ['S26LCA', 'S26LCAMIX'] )
                   and ( adjGrossVolSpeciesId in [101, 109, 119, 127, 137]))                   
                      
                or (( region_id in ['S26LCA', 'S26LCAMIX', 'S26LWOR', 'S26LORJJ'])
                      and ( adjGrossVolSpeciesId in [116, 122]))

                or (( region_id in ['S26LCA', 'S26LCAMIX', 
                                    'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                    'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( adjGrossVolSpeciesId == 117))):

                # TODO implement the calculation here
                print('Table 4 Row 8')

            # Table 4 Row 9
            elif ((( region_id == 'S26LEOR' )
                   and ( adjGrossVolSpeciesId == 116))                   
                      
                or (( region_id in ['S26LEOR', 'S26LEWA', 'S26LWWA', 'S26LWACF'])
                      and ( adjGrossVolSpeciesId == 122))

                or (( region_id in ['S26LEOR', 'S26LEWA'])
                      and ( adjGrossVolSpeciesId == 202))):

                # TODO implement the calculation here
                print('Table 4 Row 9')

            # Table 4 Row 10
            elif (( region_id in ['S26LCA', 'S26LCAMIX']  )
                   and ( adjGrossVolSpeciesId in [201, 202])):

                # TODO implement the calculation here
                print('Table 4 Row 10')

             # Table 4 Row 11
            elif (( region_id in ['S26LWOR', 'S26LORJJ', 'S26LWWA', 'S26LWACF']  )
                   and ( adjGrossVolSpeciesId == 202)):

                # TODO implement the calculation here
                print('Table 4 Row 11')

             # Table 4 Row 12
            elif (( region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LWOR', 'S26LORJJ']  )
                   and ( adjGrossVolSpeciesId in [211, 212])):

                # TODO implement the calculation here
                print('Table 4 Row 12')

            # Table 4 Row 13
            elif (( region_id in ['S26LCA', 'S26LCAMIX', 
                                  'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                  'S26LEWA', 'S26LWWA', 'S26LWACF'])
                   and ( adjGrossVolSpeciesId == 263)):

                # TODO implement the calculation here
                print('Table 4 Row 13')

            # Table 4 Row 14
            elif (( region_id in ['S26LCA', 'S26LCAMIX', 
                                  'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                  'S26LEWA', 'S26LWWA', 'S26LWACF'])
                   and ( adjGrossVolSpeciesId in [264, 299])):

                # TODO implement the calculation here
                print('Table 4 Row 14')   

            # Table 4 Row 15
            elif (( region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LWOR', 'S26LORJJ'])
                   and ( adjGrossVolSpeciesId in [312, 313, 361, 431, 540, 
                                                   542, 815, 818, 901, 997])
                   
                or ((region_id == 'S26LWOR')
                    and adjGrossVolSpeciesId == 320 )

                or ((region_id in ['S26LCA', 'S26LCAMIX'])
                    and adjGrossVolSpeciesId in [330, 333, 421, 492, 500, 
                                                  600, 602, 660, 661, 730, 
                                                  763, 801, 807, 811, 826, 
                                                  839, 920, 998, 999] )

                or ((region_id in ['S26LCA', 'S26LCAMIX', 'S26LWOR', 'S26LORJJ'])
                    and adjGrossVolSpeciesId in [631, 805, 981])
                    
                or ((region_id == 'S26LCA')
                    and adjGrossVolSpeciesId in [547, 604, 731, 922])

                or ((region_id in ['S26LCA', 'S26LCAMIX', 'S26LWOR', 'S26LEWA'])
                    and adjGrossVolSpeciesId == 603)

                or ((region_id in ['S26LCA', 'S26LCAMIX', 'S26LORJJ'])
                    and adjGrossVolSpeciesId == 821)):

                # TODO implement the calculation here
                print('Table 4 Row 15')

            # Table 4 Row 16
            elif (( region_id in ['S26LEWA', 'S26LWWA', 'S26LWACF'])
                   and ( adjGrossVolSpeciesId in [312, 313, 370, 431, 540,
                                                   542, 815, 901, 997])
                   
                or ((region_id == 'S26LWOR')
                    and adjGrossVolSpeciesId in [351, 926] )

                or ((region_id in ['S26LWWA', 'S26LWACF'])
                    and adjGrossVolSpeciesId == 361 )

                or ((region_id in ['S26LCA', 'S26LCAMIX', 
                                  'S26LEOR', 'S26LWOR', 'S26LORJJ',
                                  'S26LEWA', 'S26LWWA', 'S26LWACF'] )
                    and adjGrossVolSpeciesId in [374, 375, 591])
                    
                or ((region_id in ['S26LEOR', 'S26LWOR', 'S26LORJJ',
                                   'S26LEWA', 'S26LWWA', 'S26LWACF'] )
                    and adjGrossVolSpeciesId in [492, 500, 602, 660, 661, 
                                                  730, 746, 747, 760, 763,
                                                  766, 768, 920, 998, 999])

                or ((region_id in ['S26LWOR', 'S26LORJJ'])
                    and adjGrossVolSpeciesId == 510)

                or ((region_id in ['S26LEOR', 'S26LWOR', 'S26LORJJ', 'S26LWWA', 'S26LWACF'])
                    and adjGrossVolSpeciesId == 600)

                or ((region_id in ['S26LEOR', 'S26LWWA', 'S26LWACF'])
                    and adjGrossVolSpeciesId == 631)

                or ((region_id == 'S26LEWA')
                     and adjGrossVolSpeciesId == 818)):

                # TODO implement the calculation here
                print('Table 4 Row 16')

            # Table 4 Row 17
            elif (( region_id in ['S26LCA', 'S26LCAMIX'])
                   and ( adjGrossVolSpeciesId == 510)
                   
                or (region_id == 'S26LCA')
                    and adjGrossVolSpeciesId == 511 ):

                # TODO implement the calculation here
                print('Table 4 Row 17')   

            # Table 4 Row 18
            elif (( region_id in ['S26LCA', 'S26LCAMIX'])
                   and ( adjGrossVolSpeciesId == 756)
                   
                or ((region_id == 'S26LCA')
                    and adjGrossVolSpeciesId == 758 )
                    
                or ((region_id in ['S26LCA', 'S26LCAMIX', 'S26LEOR', 'S26LEWA'])
                    and adjGrossVolSpeciesId == 990 )                
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

        return volcfgrs


if __name__ == '__main__':
    crm = Component_Ratio_Method()
    species = crm._getSpeciesData(58)
    print(crm._getGrossVolCoeff(66, 'S23LCS'))



