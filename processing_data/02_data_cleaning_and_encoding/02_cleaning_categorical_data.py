
import sys
import pandas as pd
import numpy as np
import inspect
# from itertools import ifilter


"""# Standardising entries

We will correct recurrent errors in the descriptions and translate/remove the Welsh in the entries.
"""

class CleaningCategoricalData():
	def __init__(self, df):
		self.df = df

	def select_cat_var(self):
		"""Get list of categorical variables to clean."""

		self.cat_var = self.df.select_dtypes(include= ['object']).columns.tolist()

		print(self.cat_var)

		# Not these variables
		self.cat_var.remove('address')
		self.cat_var.remove('postcode')
		self.cat_var.remove('msoa_code')
		self.cat_var.remove('lsoa_code')
		self.cat_var.remove('constituency')

		# not categorical
		if 'inspection-date' in self.cat_var:
			self.cat_var.remove('inspection-date')
		if 'lodgement-datetime' in self.cat_var:
			self.cat_var.remove('lodgement-datetime')
		self.cat_var.remove('solar-water-heating-flag')
		self.cat_var.remove('photo-supply-binary')
		self.cat_var.remove('mains-gas-flag')

	def remove_bilingual(self):
		"""Remove Welsh text that comes after |."""
		for c in self.cat_var:
			self.df[c] = self.df[c].str.replace(r"\|(.*)", "")

	def general_desc_cleaning(self):
		"""General cleaning for three description variables."""

		for c in ['floor-description','walls-description','roof-description']:
			# standardising the unit used
			self.df[c] = self.df[c].str.replace(r"W(.*?)K",'W/m²K')
			# removing nonsense 
			self.df[c] = self.df[c].str.replace("\*\*\* INVALID INPUT Code \: 57 \*\*\*","")
			# cleaning up 
			self.df[c] = self.df[c].str.replace(r'\.$','')
			self.df[c] = self.df[c].str.replace(r'\,$','')
			self.df[c] = self.df[c].str.replace("  \+"," +")
			self.df[c] = self.df[c].str.replace("[ \t]+$","")
			self.df[c] = self.df[c].str.replace('  ',' ')
			self.df[c] = self.df[c].str.replace('Average thermal transmittance 1 ','Average thermal transmittance 1.00 ')
			self.df[c] = self.df[c].str.replace('Average thermal transmittance =','Average thermal transmittance')
			self.df[c] = self.df[c].str.rstrip(' ')
			# Lower all case
			self.df[c] = self.df[c].str.lower()

	def walls_description(self):
		# translating welsh sentences
		self.df['walls-description'] = self.df['walls-description'].str.replace("waliau ceudod","cavity wall")
		self.df['walls-description'] = self.df['walls-description'].str.replace("dim inswleiddio","no insulation")
		self.df['walls-description'] = self.df['walls-description'].str.replace("tywoself.dfaen","sandstone")
		self.df['walls-description'] = self.df['walls-description'].str.replace(r"ceudod wedi(.*?)i lenwi","filled cavity")
		self.df['walls-description'] = self.df['walls-description'].str.replace(r"wedi(.*?)u hinswleiddio","insulated")
		self.df['walls-description'] = self.df['walls-description'].str.replace(r"ffr(.*?)m bren","timber frame")
		self.df['walls-description'] = self.df['walls-description'].str.replace("briciau solet","solid brick")
		self.df['walls-description'] = self.df['walls-description'].str.replace(r"wedi(.*?)u hadeiladu yn (.*?)l system","system built")
		self.df['walls-description'] = self.df['walls-description'].str.replace("inswleiddio rhannol","partial insulation")
		self.df['walls-description'] = self.df['walls-description'].str.replace("gydag inswleiddio allanol","with external insulation")
		self.df['walls-description'] = self.df['walls-description'].str.replace("gwenithfaen neu risgraig","granite or whinstone")
		self.df['walls-description'] = self.df['walls-description'].str.replace("gydag inswleiddio mewnol","with internal insulation")
		self.df['walls-description'] = self.df['walls-description'].str.replace(r"\(rhagdybiaeth\)","(assumed)")
		self.df['walls-description'] = self.df['walls-description'].str.replace(r"fel y(.*?)u hadeiladwyd, ","")

		# removing phrases like as built which aren't adding anything
		self.df['walls-description'] = self.df['walls-description'].str.replace(r"\(assumed\)","")
		self.df['walls-description'] = self.df['walls-description'].str.replace("as built, ","")
		self.df['walls-description'] = self.df['walls-description'].str.replace(", as built","")
		self.df['walls-description'] = self.df['walls-description'].str.replace(r"cavity\.","cavity wall,")

		# standardising punctuation
		self.df['walls-description'] = self.df['walls-description'].str.replace(r"solid brick\.","solid brick,")

		# standardising language
		self.df['walls-description'] = self.df['walls-description'].replace(
			regex=["granite or whin,", "stone \(granite or whin\)\."],
			value="granite or whinstone,")
		self.df['walls-description'] = self.df['walls-description'].replace(
			regex=["with external insulation", "with internal insulation", 
			"with additional insulation", "with insulation"],
			value="insulated")

		# clean up
		self.df['walls-description'] = self.df['walls-description'].str.replace(r'\+ chr\(13\) \+','+')
		self.df['walls-description'] = self.df['walls-description'].str.replace(r"[ \t]+$","")
		self.df['walls-description'] = self.df['walls-description'].str.replace(r'timber frame\.','timber frame,')
		self.df['walls-description'] = self.df['walls-description'].str.replace(r'\?','')
		self.df['walls-description'] = self.df['walls-description'].str.replace(r'system built\.','system built,')

	def roof_description(self):
		# standardising units
		self.df['roof-description'] = self.df['roof-description'].str.replace(" mm",'mm')
		self.df['roof-description'] = self.df['roof-description'].str.replace(">= 300mm",">=300mm")
		self.df['roof-description'] = self.df['roof-description'].str.replace(">=300mm","300+mm")

		# translating welsh sentences
		self.df['roof-description'] = self.df['roof-description'].str.replace(r"\|\(eiddo arall uwchben\)","")
		self.df['roof-description'] = self.df['roof-description'].str.replace("ar oledself.df","pitched")
		self.df['roof-description'] = self.df['roof-description'].str.replace("dim inswleiddio","no insulation")
		self.df['roof-description'] = self.df['roof-description'].str.replace(r"wedi(.*?)i inswleiddio","insulated")
		self.df['roof-description'] = self.df['roof-description'].str.replace("(rhagdybiaeth)","assumed")
		self.df['roof-description'] = self.df['roof-description'].str.replace(r"lo inswleiddio yn y llof.*","loft insulation")
		self.df['roof-description'] = self.df['roof-description'].str.replace(r"o inswleiddio yn y llof.*","loft insulation")
		self.df['roof-description'] = self.df['roof-description'].str.replace(r"ystafell\(oedd\) to","roof room(s)")
		self.df['roof-description'] = self.df['roof-description'].str.replace(r"wedi(.*?)i hinswleiddio","insulated")
		self.df['roof-description'] = self.df['roof-description'].str.replace("nenfwd","ceiling")
		self.df['roof-description'] = self.df['roof-description'].str.replace(r"wrth y trawstia(.*?)","at rafters")
		self.df['roof-description'] = self.df['roof-description'].str.replace("inswleiddio cyfyngedig","limited insulation")
		self.df['roof-description'] = self.df['roof-description'].str.replace("to gwellt, gydag inswleiddio ychwanegol","thatched, with additional insulation")
		self.df['roof-description'] = self.df['roof-description'].str.replace("yn wastad","always")
		self.df['roof-description'] = self.df['roof-description'].str.replace("annedd arall uwchben","other premises above")

		# standardising descriptions
		self.df['roof-description'] = self.df['roof-description'].str.replace("roof room,","roof room(s),")
		self.df['roof-description'] = self.df['roof-description'].str.replace("another dwelling above","other premises above")
		self.df['roof-description'] = self.df['roof-description'].replace(
			regex=["other premises above","dwelling Above"],
			value="(other premises above)")
		self.df['roof-description'] = self.df['roof-description'].str.replace("0 w/m²k"," w/m²k")
		self.df['roof-description'] = self.df['roof-description'].str.replace("  w/m²k"," 0.0 w/m²k")
		self.df['roof-description'] = self.df['roof-description'].str.replace(r"roof room\(s\), no insulation\(assumed\)","roof room(s), no insulation (assumed)")
		self.df['roof-description'] = self.df['roof-description'].str.replace(r"\(assumed\)","")
		self.df['roof-description'] = self.df['roof-description'].str.replace("0mm loft","no")

		# cleanup
		self.df['roof-description'] = self.df['roof-description'].str.replace("mmmm","mm")
		self.df['roof-description'] = self.df['roof-description'].str.replace(r"\({2,}",r"\(")
		self.df['roof-description'] = self.df['roof-description'].str.replace(r"\){2,}",r"\)")
		self.df['roof-description'] = self.df['roof-description'].str.replace(",mm",",")
		self.df['roof-description'] = self.df['roof-description'].str.replace("thatchedinsulated","thatched, insulated")
		self.df['roof-description'] = self.df['roof-description'].str.rstrip(" ")

		self.df['roof-description'].value_counts()

	def floor_description(self):
		# translating welsh sentences
		self.df['floor-description'] = self.df['floor-description'].str.replace(r"anheddiad arall islaw",'another dwelling below') 
		self.df['floor-description'] = self.df['floor-description'].str.replace(r"\(eiddo arall islaw\)",'other premises below') 
		self.df['floor-description'] = self.df['floor-description'].str.replace(r"wedi(.*?)i inswleiddio","insulated")
		self.df['floor-description'] = self.df['floor-description'].str.replace("dim inswleiddio","no insulation")
		self.df['floor-description'] = self.df['floor-description'].str.replace("(rhagdybiaeth)","assumed")
		self.df['floor-description'] = self.df['floor-description'].str.replace("crog","suspended")
		self.df['floor-description'] = self.df['floor-description'].str.replace("heb ei inswleiddio","no insulation")
		self.df['floor-description'] = self.df['floor-description'].str.replace("i ofod heb ei wresogi","to unheated space")
		self.df['floor-description'] = self.df['floor-description'].str.replace("solet","solid")
		self.df['floor-description'] = self.df['floor-description'].str.replace("inswleiddio cyfyngedig","limited insulation")

		# removing assumed
		self.df['floor-description'] = self.df['floor-description'].str.replace(r"\(assumed\)","")

		# standardising language
		self.df['floor-description'] = self.df['floor-description'].replace(
			regex=["\(another dwelling below\)", "\(other premises below\)"],
			value='other premises below') 
		self.df['floor-description'] = self.df['floor-description'].str.replace(r"solid\.",'solid,') 
		self.df['floor-description'] = self.df['floor-description'].str.replace("uninsulated",'no insulation,') 
		self.df['floor-description'] = self.df['floor-description'].str.replace("insulation=100mm",'100 mm insulation') 
		self.df['floor-description'] = self.df['floor-description'].str.replace(r"\, \(assumed\)",' (assumed)')
		self.df['floor-description'] = self.df['floor-description'].str.replace("insulation=25mm",'25 mm insulation')
		self.df['floor-description'] = self.df['floor-description'].str.replace("insulation=75mm",'75 mm insulation')
		self.df['floor-description'] = self.df['floor-description'].str.replace("limited insulated",'limited insulation')
		self.df['floor-description'] = self.df['floor-description'].str.replace("(same dwelling below) ", "")
		# cleanup
		self.df['floor-description'] = self.df['floor-description'].str.replace(r'^, ','')
		self.df['floor-description'] = self.df['floor-description'].str.replace(r'\?','')
		self.df['floor-description'] = self.df['floor-description'].str.rstrip(' ,.')

	def extract_thermal_transmittance(self):
		# Extract thermal transmittance feature
		##improve null##
		for c in ['floor-description','walls-description','roof-description']:
			col_name = c.split('-')[0] + "-thermal-transmittance"
			transmittance_col = self.df[c].str.findall(r'(\d.\d*) W/m²K')
			self.df[col_name] = round(transmittance_col.str[0].astype(float),2)

	def construction_age_band(self):
		construction_year = self.df['construction-age-band'].str.findall(r"(\d{4})")
		self.df['construction-age-band'] = construction_year.str[-1].astype('datetime64')

		self.cat_var.remove('construction-age-band')

	def transaction_type(self):
		self.df['transaction-type'] = self.df['transaction-type'].str.replace(" - this is for backwards compatibility only and should not be used","")
		self.df['transaction-type'] = self.df['transaction-type'].str.replace("Stock Condition Survey", "Stock condition survey")
		self.df['transaction-type'] = self.df['transaction-type'].replace("not recorded", np.nan)

	def main_fuel(self):
		# standardising language
		self.df['main-fuel'] = self.df['main-fuel'].str.replace('Gas: ', '')
		self.df['main-fuel'] = self.df['main-fuel'].str.replace(r'Electricity\:.*', 'electricity')

		# cleanup
		self.df['main-fuel'] = self.df['main-fuel'].str.replace(" - this is for backwards compatibility only and should not be used","")
		self.df['main-fuel'] = self.df['main-fuel'].replace('To be used only when there is no heating/hot-water system', np.nan)
		self.df['main-fuel'] = self.df['main-fuel'].replace('To be used only when there is no heating/hot-water system or data is from a community network', np.nan)

	def tenure(self):
		self.df['tenure'] = self.df['tenure'].str.replace('Rented', 'rental')
		self.df['tenure'] = self.df['tenure'].replace('Not defined - use in the case of a new dwelling for which the intended tenure in not known. It is no', np.nan)
		self.df['tenure'] = self.df['tenure'].str.lower()

	def floor_level(self):
		# Standardising floors
		self.df['floor-level'] = self.df['floor-level'].replace(
			regex=[r'(?<=\d)th', r'(?<=\d)nd', r'(?<=\d)rd', r'(?<=\d)st'], 
			value='')
		self.df['floor-level'] = self.df['floor-level'].str.lstrip('0')
		self.df['floor-level'] = self.df['floor-level'].replace(
			regex=['ground floor', r'^\s*$'], 
			value='Ground')
		self.df['floor-level'] = self.df['floor-level'].replace('Basement', '-1')
	
	def glazed_area(self):
		self.df['glazed-area'] = self.df['glazed-area'].replace('Not Defined', np.nan)

	def mainheatcont_description(self):
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.lower()

		# translating welsh sentences
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace(r"rheoli.r t.l . llaw","manual charge control")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("rhaglennydd, dim thermostat ystafell","programmer, no room thermostat")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("rheolaeth amser a rheolaeth parthau tymheredd","time and temperature zone control")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("rhaglennydd a thermostat ystafell","programmer and room thermostat")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("rhaglennydd a thermostatau ar y cyfarpar","programmer and appliance thermostats")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("rhaglennydd ac o leiaf ddau thermostat ystafell","programmer and at least two room thermostats")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("thermostat ystafell yn unig","room thermostat only")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("dim rheolaeth thermostatig ar dymheredd yr ystafell","no thermostatic control of room temperature")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("rheoli gwefr drydanol yn awtomatig","automatic charge control")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("dim rheolaeth amser na rheolaeth thermostatig ar dymheredd yr ystafell","no time or thermostatic control of room temperature")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("trvs a falf osgoi","trvs and bypass")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("rhaglennydd","programmer")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("tal un gyfradd, thermostat ystafell yn unig","flat rate charging, room thermostat only")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("thermostat ystafell a trvs","room thermostat and trvs")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace(r"t(.*?)l un gyfradd","flat rate charging")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("thermostatau ar y cyfarpar","appliance thermostat")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("dim","none")

		# standardising language
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("programmer, no thermostat","programmer, no room thermostat")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("flat rate charging\*","flat rate charging")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].replace(
			regex=[r"\+",r"\&"] ,
			value="and")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("trv.s","trvs")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].replace(
			regex=["thermostats", " stat", "thermostatic"],
			value="thermostat")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("communit ","community ")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("to the use of community heating","to use of community heating")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("controls","control")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].replace(
			regex=["prog ","program "],
			value="programmer ")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].replace(
			regex=["programmerand",r"programmer\?and"],
			value="programmer and")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("roomthermostat","room thermostat")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("delayed start thermostat and program and trvs","delayed start thermostat, program and trvs")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("flat rate charging, programmer no room thermostat","flat rate charging, programmer, no room thermostat")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace(" 2 "," two ")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("roomstat","room thermostat")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("programmer and room thermostat and trvs","programmer, room thermostat and trvs")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("programmer and trvs and boiler energy manager","programmer, trvs and boiler energy manager")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("programmer and trvs and bypass","programmer, trvs and bypass")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("programmer and trvs and flow switch","programmer, trvs and flow switch")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace(r"temp+$","temperature")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("no thermostat control of room temperature","no thermostat control")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("appliance thermostat and programmer","programmer and appliance thermostat")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("delayed start thermostat and programmer and trvs","delayed start thermostat, programmer and trvs")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("no time or thermostat control of temperature","no time or thermostat control of room temperature")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("nothermostat","no thermostat")
		self.df['mainheatcont-description'] = self.df['mainheatcont-description'].str.replace("at least two room thermostat","at least two room thermostats")

	def hotwater_description(self):
		# translating welsh sentences
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"O(.*?)r brif system","From main system")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"Trochi trydan","Electric immersion")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"an-frig","off-peak")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"O system eilaidd","From secondary system")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"Nwy wrth fwy nag un pwynt","Gas multipoint")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"Popty estynedig olew","Oil range cooker")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"tarriff safonol","standard tariff")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"Dim system ar gael","No system present")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"aself.dfer gwres nwyon ffliw","flue gas heat recovery")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"gydag ynni(.*?)r haul","plus solar")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"dim thermostat ar y silindr","no cylinderstat")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"rhagdybir bod twymwr tanddwr trydan","electric immersion assumed")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"an-frig","off peak")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace(r"Twymwr tanddwr","underfloor heating")

		# Standardising language
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace("cylinder thermostat","cylinderstat")
		self.df['hotwater-description'] = self.df['hotwater-description'].replace(
			regex=["No system present :", "No hot water system present -"],
			value="No system present:")
		self.df['hotwater-description'] = self.df['hotwater-description'].replace(
			regex=["From community scheme", "community scheme"],
			value="Community scheme")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace("Community heat pump","Community scheme with CHP")
		self.df['hotwater-description'] = self.df['hotwater-description'].replace(
			regex=["From secondary heater","From second main heating system"],
			value="From secondary system")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace("SAP05:Hot-Water","SAP:Hot-Water")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace("plus solar, no cylinderstat","no cylinderstat, plus solar")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace("none","No system present: electric immersion assumed")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace("plus solar, flue gas heat recovery","flue gas heat recovery, plus solar")
		self.df['hotwater-description'] = self.df['hotwater-description'].str.replace("no cylinderstat, no cylinderstat","no cylinderstat")

		# cleanup
		self.df['hotwater-description'] = self.df['hotwater-description'].replace("***SAMPLE***",np.nan)
		self.df['hotwater-description'] = self.df['hotwater-description'].str.strip(" .,")

	def windows_description(self):
		self.df['windows-description'] = self.df['windows-description'].str.lower()

		# translating welsh sentences
		self.df['windows-description'] = self.df['windows-description'].str.replace("ffenestri perfformiad uchel","high performance glazing")
		self.df['windows-description'] = self.df['windows-description'].str.replace("gwydrau dwbl gan mwyaf","mostly double glazing")
		self.df['windows-description'] = self.df['windows-description'].str.replace("rhai gwydrau dwbl","partial double glazing")
		self.df['windows-description'] = self.df['windows-description'].str.replace("gwydrau sengl","single glazing")
		self.df['windows-description'] = self.df['windows-description'].str.replace("gwydrau dwbl rhannol","partial double glazing")
		self.df['windows-description'] = self.df['windows-description'].str.replace("gwydrau dwbl llawn","fully double glazing")
		self.df['windows-description'] = self.df['windows-description'].str.replace("gwydrau lluosog ym mhobman","multiple glazing throughout")
		self.df['windows-description'] = self.df['windows-description'].str.replace("gwydrau eilaidd llawn","full secondary glazing")

		# Standardising language
		self.df['windows-description'] = self.df['windows-description'].str.replace("glazed","glazing")
		self.df['windows-description'] = self.df['windows-description'].str.replace("fully","full")

		# clean-up
		self.df['windows-description'] = self.df['windows-description'].str.replace("single glazingsingle glazing","single glazing")
		self.df['windows-description'] = self.df['windows-description'].str.replace("single glazingdouble glazing","single glazing and double glazing")
		self.df['windows-description'] = self.df['windows-description'].str.replace("single glazingsecondary glazing","single glazing and secondary glazing")
		self.df['windows-description'] = self.df['windows-description'].str.replace("  "," ")

	def lighting_description(self):
		self.df['secondheat-description1'] = self.df.apply(lambda row: row['lighting-description'] if 'lighting' in str(row['secondheat-description']) else row['secondheat-description'],axis = 1)
		self.df['lighting-description1'] = self.df.apply(lambda row: row['secondheat-description'] if 'lighting' in str(row['secondheat-description']) else row['lighting-description'],axis = 1)
		self.df.drop(columns= ['secondheat-description','lighting-description'],axis=1,inplace=True)
		self.df.rename(columns={'secondheat-description1':'secondheat-description','lighting-description1':'lighting-description'},inplace=True)

		self.df['lighting-description'] = self.df['lighting-description'].str.lower()

		# Converting lighting descriptions in % of low energy lighting
		self.df['lighting-description'] = self.df['lighting-description'].str.replace(r'goleuadau ynni-isel ym mhob un o.r mannau gosod','low energy lighting in 100% fixed outlets')
		self.df['lighting-description'] = self.df['lighting-description'].str.replace(r'low energy lighting in 120% of fixed outlets','low energy lighting in 100% fixed outlets')
		self.df['lighting-description'] = self.df['lighting-description'].str.replace(r'low energy lighting 100% of fixed outlets','low energy lighting in 100% fixed outlets')
		self.df['lighting-description'] = self.df['lighting-description'].str.replace(r'no low energy lighting','low energy lighting in 0% fixed outlets')
		self.df['lighting-description'] = self.df['lighting-description'].str.replace('dim goleuadau ynni-isel', 'low energy lighting in 0% fixed outlets')

		# Extract % low energy lighting
		self.df['percentage-low-energy-lighting'] = self.df['lighting-description'].str.extract('([-+]?(?:\d*\.\d+|\d+))')
		self.df['percentage-low-energy-lighting'] = self.df['percentage-low-energy-lighting'].astype(float)

	def secondheat_description(self):
		# standardise language
		self.df['secondheat-description'] = self.df['secondheat-description'].str.rstrip(', ')
		self.df['secondheat-description'] = self.df['secondheat-description'].str.replace('LNG', 'LPG')
		self.df['secondheat-description'].replace(regex=[r'\,\s\(null\)', r'\s*\(assumed\)'], value='', inplace=True)

		# translate welsh
		self.df['secondheat-description'] = self.df['secondheat-description'].str.replace('Gwresogyddion ystafell, nwy prif gyflenwad', 'Room heaters, mains gas')
		self.df['secondheat-description'] = self.df['secondheat-description'].str.replace('Gwresogyddion ystafell, trydan', 'Room heaters, electric')
		self.df['secondheat-description'] = self.df['secondheat-description'].str.replace('Gwresogyddion trydan cludadwy', 'Portable electric heaters')

		self.df['secondheat-description'] = self.df['secondheat-description'].str.lower()

	def main_heating_controls(self):
		self.df['main-heating-controls'] = self.df['main-heating-controls'].replace('%%MAINHEATCONTROL%%', np.nan)
		self.df['main-heating-controls'] = self.df['main-heating-controls'].astype(float)

		self.cat_var.remove('main-heating-controls')


	def mainheat_description(self):

		elec_list = ["Electric storage heaters", "Room heaters, electric", "Boiler and radiators, electric", "Electric underfloor heating", 
						"No system present: electric heaters assumed", "Warm air, electric", "Portable electric heating assumed for most rooms",
						"Ground source heat pump, warm air, electric", "Water source heat pump, warm air, electric", "Warm air, Electricaire",
						"Portable electric heaters assumed for most rooms", "Boiler and underfloor heating, electric", "Ground source heat pump, radiators, electric",
						"Electric Underfloor Heating (Standard tariff), electric", "Portable electric heaters", "Water source heat pump, radiators, electric",
						"Air source heat pump, radiators, electric", "Air source heat pump, ratiators, electric",
						"Air source heat pump, underfloor, electric", "Electric ceiling heating", "Ground source heat pump, underfloor, electric",
						"Air source heat pump,", "Boiler and underfloor heating, mains gas, Air source heat pump, warm air, electric", "Room heaters,", 
						"Water source heat pump, underfloor, mains gas", "Room heaters, electricity", "Air source heat pump, radiators, electricity",
						"Air source heat pump, , radiators, electric", "No system present: electric heaters assumed, radiators", 
						"Portable electric heating assumed for most rooms, electric", "Air source heat pump, fan coil units, electric",
						"Electric ceiling heating, electric", "Room heaters", "Air source heat pump, warm air, electric", "Electric ceiling heating, underfloor, electric",
						"Ground source heat pump, Underfloor heating and radiators, pipes in screed above insulation, electric", "Electric storage heaters, radiators",
						"Electric heat pumps, electric", "Air source heat pump, Underfloor heating, pipes in screed above insulation, electric", "Electric storage heaters, underfloor",
						"Room heaters, radiators, electric", "Ground source heat pump, radiators, mains gas", "Air source heat pump, Systems with radiators, electric", 
						"Air source heat pump, Underfloor heating and radiators, pipes in screed above insulation, electric",
						"Air source heat pump, Underfloor heating, pipes in insulated timber floor, electric", "Boiler & underfloor, electric", "Air source heat pump , electric",
						"Water source heat pump, underfloor, electric", "Boiler and radiators, mains gas, Air source heat pump, underfloor, electric", 
						"Room heaters, electric, Electric storage heaters", "Electric storage heaters, Electric storage heaters",
						"Electric storage heaters, Room heaters, electric", "Room heaters, electric, Room heaters, electric",
						"Air source heat pump, radiators, electric, Air source heat pump, underfloor, electric", "Electric storage heaters, Electric underfloor heating",
						"Portable electric heaters assumed for most rooms, Room heaters, electric", "Ground source heat pump, underfloor, mains gas", 
						"Electric underfloor heating, Room heaters, electric", "Water source heat pump, radiators, mains gas", "Boiler and underfloor heating, oil, Air source heat pump, warm air, electric",
						"Air source heat pump, ", "Room heaters, "]

		non_elec_list = ["Boiler and radiators, mains gas", "Boiler and underfloor heating, mains gas", "Warm air, mains gas", "Room heaters, mains gas",
							"Boiler and radiators, oil", "Boiler and radiators, LPG", "Boiler and radiators, dual fuel (mineral and wood)", "Room heaters, oil",
							"Room heaters, coal", "Room heaters, dual fuel (mineral and wood)", "Room heaters, smokeless fuel", "Boiler and radiators, coal",
							"Community scheme, mains gas", "Boiler and underfloor heating, LPG", "Boiler and radiators, smokeless fuel", "Room heaters, wood logs",
							"Warm air, oil", "Boiler and radiators, wood logs", "Community scheme, radiators, mains gas", "Boiler and radiators, wood chips",
							"Boiler, mains gas", "Boiler and underfloor heating, oil", "Warm air, LPG", "Room heaters, LPG", "Boiler and radiators, bottled LPG",
							"Micro-cogeneration, mains gas", "Boiler and radiators, wood pellets", "Air source heat pump, warm air, mains gas", "Boiler & underfloor, mains gas",
							"Room heaters, bottled LPG", "Room heaters, wood chips", "Boiler and underfloor heating, wood logs", "Boiler & underfloor, wood pellets",
							"Boiler & underfloor, oil", "Boiler and radiators, mains gas, Boiler and radiators, mains gas", "Warm air, mains gas, Boiler and radiators, mains gas",
							"Boiler and radiators, mains gas, Boiler and underfloor heating, mains gas", "Boiler and radiators, mains gas, Room heaters, wood logs",
							"Boiler and underfloor heating, mains gas, Boiler and radiators, mains gas", "Boiler and radiators, mains gas, Room heaters, mains gas",
							"Boiler & underfloor, LPG", "Room heaters, mains gas, Room heaters, mains gas", "Boiler and underfloor heating, mains gas, Boiler and underfloor heating, mains gas",
							"Boiler & underfloor, mains gas, Boiler And underfloor heating, mains gas", "Room heaters, mains gas, Room heaters, coal", "Room heaters, mains gas, Room heaters, anthracite",
							"Room heaters, mains gas, Room heaters, smokeless fuel", "Room heaters, mains gas, Room heaters, dual fuel (mineral and wood)", "Community scheme with CHP",
							"Community scheme with CHP and mains gas", "Community scheme with CHP, mains gas", "Boiler and radiators, anthracite", "Room heaters, anthracite",
							"Boiler, anthracite", "Boiler and radiators, B30K", "Bwyler a rheiddiaduron, nwy prif gyflenwad", "Awyr gynnes, nwy prif gyflenwad", "No system present: electric heaters assumed, mains gas", 
							"No system present: electric heaters assumed, gas", "Room heaters, dual fuel (mineral and wood), Electric storage heaters",
							"Boiler and radiators, mains gas, Electric storage heaters", "Room heaters, mains gas, Room heaters, electric", "Boiler and radiators, mains gas, Electric underfloor heating",
							"Electric storage heaters, Room heaters, mains gas", "Warm air, mains gas, Electric storage heaters", "Boiler and radiators, mains gas, Boiler and radiators, electric",
							"Boiler and underfloor heating, mains gas, Room heaters, electric", "Boiler and radiators, mains gas, Room heaters, electric",
							"Room heaters, electric, Room heaters, mains gas", "Room heaters, mains gas, Electric storage heaters", "Room heaters, coal, Room heaters, electric",
							"Room heaters, electric, Room heaters, coal", "Room heaters, electric, Room heaters, dual fuel (mineral and wood)",
							"Room heaters, electric, Room heaters, smokeless fuel", "Electric storage heaters, Boiler and radiators, mains gas", 
							"Electric storage heaters, Room heaters, smokeless fuel", "Community, community", "Community scheme", "SAP05:Main-Heating", "Boiler and radiators", "Boiler and radiators, "]


		# replace list objects with electric, non-electric, mixed, or unknown
		for elec in elec_list:
			self.df['mainheat-description'] = self.df['mainheat-description'].replace(elec,1)
		for non_elec in non_elec_list:
			self.df['mainheat-description'] = self.df['mainheat-description'].replace(non_elec,0)
		

	def check_cleaning(self):
		"""Check that cleaning is done correctly."""
		for c in self.cat_var:
			print(f'\nVariable: {c}')
			print(self.df[c].unique())

	def process(self):
		# pulling all the functions together
		self.select_cat_var()
		self.remove_bilingual()
		self.general_desc_cleaning()
		self.walls_description()
		self.roof_description()
		self.floor_description()
		self.extract_thermal_transmittance()
		self.construction_age_band()
		self.transaction_type()
		self.main_fuel()
		self.tenure()
		self.floor_level()
		self.glazed_area()
		self.mainheatcont_description()
		self.hotwater_description()
		self.windows_description()
		self.lighting_description()
		self.secondheat_description()
		self.main_heating_controls()
		self.mainheat_description()
		self.check_cleaning()

		return self.df


def main(df):
	cleaning = CleaningCategoricalData(df)
	attrs = (getattr(cleaning, name) for name in dir(cleaning))
	# methods = ifilter(inspect.ismethod, attrs)
	# for method in methods:
	# 	method()

if __name__ == "__main__":
	main()