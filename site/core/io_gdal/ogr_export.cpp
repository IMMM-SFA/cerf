
///////////////////////////////////////////////////////////
//                                                       //
//                         SAGA                          //
//                                                       //
//      System for Automated Geoscientific Analyses      //
//                                                       //
//                    Module Library                     //
//                                                       //
//                       io_gdal                         //
//                                                       //
//-------------------------------------------------------//
//                                                       //
//                    ogr_export.cpp                     //
//                                                       //
//            Copyright (C) 2008 O. Conrad               //
//                                                       //
//-------------------------------------------------------//
//                                                       //
// This file is part of 'SAGA - System for Automated     //
// Geoscientific Analyses'. SAGA is free software; you   //
// can redistribute it and/or modify it under the terms  //
// of the GNU General Public License as published by the //
// Free Software Foundation; version 2 of the License.   //
//                                                       //
// SAGA is distributed in the hope that it will be       //
// useful, but WITHOUT ANY WARRANTY; without even the    //
// implied warranty of MERCHANTABILITY or FITNESS FOR A  //
// PARTICULAR PURPOSE. See the GNU General Public        //
// License for more details.                             //
//                                                       //
// You should have received a copy of the GNU General    //
// Public License along with this program; if not,       //
// write to the Free Software Foundation, Inc.,          //
// 59 Temple Place - Suite 330, Boston, MA 02111-1307,   //
// USA.                                                  //
//                                                       //
//-------------------------------------------------------//
//                                                       //
//    e-mail:     oconrad@saga-gis.de                    //
//                                                       //
//    contact:    Olaf Conrad                            //
//                Bundesstr. 55                          //
//                D-20146 Hamburg                        //
//                Germany                                //
//                                                       //
///////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////
//														 //
//														 //
//														 //
///////////////////////////////////////////////////////////

//---------------------------------------------------------
#include "ogr_export.h"


///////////////////////////////////////////////////////////
//														 //
//														 //
//														 //
///////////////////////////////////////////////////////////

//---------------------------------------------------------
COGR_Export::COGR_Export(void)
{
	Set_Name		(_TL("OGR: Export Vector Data"));

	Set_Author		(SG_T("(c) 2008 by O.Conrad"));

	CSG_String	Description, Formats;

	Description	= _TW(
		"The \"GDAL Vector Data Export\" module exports vector data to various file formats using the "
		"\"Geospatial Data Abstraction Library\" (GDAL) by Frank Warmerdam. "
		"For more information have a look at the GDAL homepage:\n"
		"  <a target=\"_blank\" href=\"http://www.gdal.org/\">"
		"  http://www.gdal.org</a>\n"
		"\n"
		"Following vector formats are currently supported:\n"
		"<table border=\"1\"><tr><th>Name</th><th>Description</th></tr>\n"
	);

	for(int i=0; i<g_OGR_Driver.Get_Count(); i++)
    {
		if( g_OGR_Driver.Can_Write(i) )
		{
			Description	+= CSG_String::Format(SG_T("<tr><td>%s</td><td>%s</td></tr>\n"),
				g_OGR_Driver.Get_Name(i).c_str(),
				g_OGR_Driver.Get_Description(i).c_str()
			);

			Formats		+= CSG_String::Format(SG_T("%s|"), g_OGR_Driver.Get_Name(i).c_str());
		}
    }

	Description	+= SG_T("</table>");

	Set_Description(Description);

	//-----------------------------------------------------
	Parameters.Add_Shapes(
		NULL, "SHAPES"	, _TL("Shapes"),
		_TL(""),
		PARAMETER_INPUT
	);

	Parameters.Add_FilePath(
		NULL, "FILE"	, _TL("File"),
		_TL(""),
		NULL, NULL, true
	);

	Parameters.Add_Choice(
		NULL, "FORMAT"	, _TL("Format"),
		_TL(""),
		Formats
	);
}

//---------------------------------------------------------
COGR_Export::~COGR_Export(void)
{}


///////////////////////////////////////////////////////////
//														 //
//														 //
//														 //
///////////////////////////////////////////////////////////

//---------------------------------------------------------
bool COGR_Export::On_Execute(void)
{
	CSG_String		File_Name;
	CSG_Shapes		*pShapes;
	COGR_DataSource	ds;

	//-----------------------------------------------------
	pShapes		= Parameters("SHAPES")	->asShapes();
	File_Name	= Parameters("FILE")	->asString();

	//-----------------------------------------------------
	if( ds.Create(File_Name, Parameters("FORMAT")->asString()) == false )
	{
		Message_Add(_TL("Could not create data source."));
	}
	else if( ds.Write_Shapes(pShapes) )
	{
		return( true );
	}

	return( false );
}


///////////////////////////////////////////////////////////
//														 //
//														 //
//														 //
///////////////////////////////////////////////////////////

//---------------------------------------------------------
