import math, sqlite3, numbers

class Component_Ratio_Method(object):

    def __init__(self):
        # uses the coefficients SQLite DB to get various species coefficients 
        self.db = 'coefficients.db'
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

        # checks for proper data types
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
                    (diameter * 2.54))

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


    def _calcDiameterInsideBark(self, species, dbh, height):

        # checks for proper data types
        self._isPositiveNumber('DBH', dbh)
        self._isPositiveNumber('Height', height)
        self._isNumber('Raile Stump DIB B1', species['raile_stump_dib_b1'])
        self._isNumber('Raile Stump DIB B2', species['raile_stump_dib_b2'])

        result = ((dbh * species['raile_stump_dib_b1']) + 
                  (dbh * species['raile_stump_dib_b2'] * (4.5 - height) / (height + 1)))

        return result


    def _calcDiameterOutsideBark(self, species, dbh, height):

        # checks for proper data types
        self._isPositiveNumber('DBH', dbh)
        self._isPositiveNumber('Height', height)
        self._isNumber('Raile Stump DOB B1', species['raile_stump_dob_b1'])

        result = dbh + (dbh * species['raile_stump_dob_b1'] * (4.5 - height) / (height + 1))

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


    def _calcStumpBiomassLbs(self, species, dbh, height):
        # todo implement this calc

        outsideVolume = (math.pi * 0.1 * self._calcDiameterOutsideBark) * 10.0
        insideVolume = (math.pi * 0.1 * self._calcDiameterInsideBark) * 10.0
        barkVolume = outsideVolume - insideVolume

        return 0


    def _calcTopBiomassJenkinsLbs(self, species, dbh, height):
        return (self._calcTotalAGBioMassJenkins(species, dbh)  - 
                self._calcStemBiomassJenkinsLbs(species, dbh)  - 
                self._calcBarkBiomassJenkinsLbs(species, dbh)  -
                self._calcFoliageBiomassJenkinsLbs(species, dbh) - 
                self._calcStumpBiomassLbs(species, dbh, height))

    def getVOLCFSND(region)

    def _calcDRYBIO_BOLE(self):


    def convertSoundVolumeToBiomass(self):
        print('convertSoundVolumeToBioMass')

    def calcBarkBiomass(self):
        print('calculateBarkBioMass')

    def calcTreeBiomass(self):
        print('calculateTreeBioMass')

    def calcStumpVolume(self):
        print('calculateStumpVolume')
    
    def calcTopBiomass(self):
        print('calculateTopBiomass')    

    def calcAdjustmentFactor(self):
        print('calculateAdjustmentFactor')       

    def applyAdjustmentFactor(self):
        print('applyAdjustmentFactor')


if __name__ == '__main__':
    crm = Component_Ratio_Method()
    print(crm.calcTotalAGBioMassJenkins(651, 7))



