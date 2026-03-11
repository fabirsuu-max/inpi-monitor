Attribute VB_Name = "Módulo1"
Option Explicit
Private Function StringQuebrarLinha(strConteudo As String, _
                                    lngQuantidadeRegistros As Long, _
                                    strEspacador As String) As String

    Dim i               As Long
    Dim strArrTmp()     As String
    Dim strRet          As String
    Dim strTmpEspacador As String
    Dim lngCont         As Long

    If strConteudo <> "" Then
        Erase strArrTmp
        strArrTmp() = Split(strConteudo, strEspacador)
        strTmpEspacador = strEspacador

        For i = 0 To UBound(strArrTmp)
            DoEvents

            If strArrTmp(i) <> "" Then

                lngCont = lngCont + 1
                
                strRet = strRet & _
                         IIf(strRet = "", "", strTmpEspacador) & _
                         strArrTmp(i)

                If lngCont >= lngQuantidadeRegistros Then
                    strTmpEspacador = vbCrLf
                    lngCont = 0
                Else
                    strTmpEspacador = strEspacador
                End If

            End If
        Next i
    End If

    StringQuebrarLinha = strRet

End Function

Public Sub PesquisaProcessarPalavras_Normal()

    Dim strRet As String
    
    '-------------------------------------------------------------
    strRet = StringPreparar_Etapa_01("C", 9, vbCrLf)

    strRet = strRet & _
             IIf(strRet = "", "", vbCrLf) & _
             StringPreparar_Etapa_01("N", 9, vbCrLf)
    
    strRet = Trim(strRet)

    If strRet <> "" Then
        strRet = StringQuebrarLinha(strRet, 10, vbCrLf)
        Call VBA_Copy_to_Clipboard(strRet)
        MsgBox "Copiar dados da área de transferência - 1"
    End If
    '-------------------------------------------------------------

    '-------------------------------------------------------------
    strRet = StringPreparar_Etapa_01("Q", 9, " ")

    If strRet <> "" Then
        Call VBA_Copy_to_Clipboard(strRet)
        MsgBox "Copiar dados da área de transferência - 2"
    End If
    '-------------------------------------------------------------

    '-------------------------------------------------------------
    strRet = StringPreparar_Etapa_01("R", 9, vbCrLf)

    If strRet <> "" Then
        Call VBA_Copy_to_Clipboard(strRet)
        MsgBox "Copiar dados da área de transferência - 3"
    End If
    '-------------------------------------------------------------

End Sub

Public Sub PesquisaProcessarPalavras_Regex()

    Dim strRet As String
    Dim strTmp As String

    '-------------------------------------------------------------
    strRet = StringPreparar_Etapa_01("C", 9, " ")

    strRet = strRet & _
             IIf(strRet = "", "", " ") & _
             StringPreparar_Etapa_01("N", 9, " ")
    
    strRet = Trim(strRet)

    If strRet <> "" Then
        strRet = StringQuebrarLinha(strRet, 20, " ")
        Call VBA_Copy_to_Clipboard(strRet)
        MsgBox "Copiar dados da área de transferência - 1"
    End If
    '-------------------------------------------------------------

    '-------------------------------------------------------------
    strRet = StringPreparar_Etapa_01("C", 9, "|")

    strRet = strRet & _
             IIf(strRet = "", "", "|") & _
             StringPreparar_Etapa_01("N", 9, "|")
    
    strRet = Trim(strRet)

    If strRet <> "" Then
        strRet = StringQuebrarLinha(strRet, 20, "|")
        Call VBA_Copy_to_Clipboard(strRet)
        MsgBox "Copiar dados da área de transferência - 2"
    End If
    '-------------------------------------------------------------

    '-------------------------------------------------------------
    strRet = StringPreparar_Etapa_01_Regex("Q", 9, "|")

    If strRet <> "" Then
        Call VBA_Copy_to_Clipboard(strRet)
        MsgBox "Copiar dados da área de transferência - 3"
    End If
    '-------------------------------------------------------------

    '-------------------------------------------------------------
    strRet = StringPreparar_Etapa_01_Regex("R", 9, "|")

    If strRet <> "" Then
        Call VBA_Copy_to_Clipboard(strRet)
        MsgBox "Copiar dados da área de transferência - 4"
    End If
    '-------------------------------------------------------------

End Sub


Private Function StringPreparar_Etapa_01(strColuna As String, _
                                         lngLinha As Long, _
                                         strEspacador As String) As String

    Dim i       As Long
    Dim strTmp  As String
    Dim strRet  As String

    i = lngLinha
    strRet = ""

    Do While UCase(Range("B" & i)) <> "FIM"
        DoEvents

        Range("A" & i).Select

        strTmp = StringPreparar_Etapa_02(strColuna, i, strEspacador)

        If strTmp <> "" Then

            strRet = strRet & _
                     IIf(strRet = "", "", strEspacador) & _
                     strTmp

        End If

        i = i + 1
    Loop

    StringPreparar_Etapa_01 = strRet

End Function
Private Function StringPreparar_Etapa_02(strColuna As String, _
                                         lngLinha As Long, _
                                         strEspacador As String) As String

    Dim i           As Long
    Dim strArrTmp() As String
    Dim strTmp      As String
    Dim strRet      As String

    strTmp = Range(strColuna & lngLinha).Value & "|"

    If strTmp <> "" And _
    strTmp <> "|" Then
        Erase strArrTmp
        strArrTmp() = Split(strTmp, "|")

        For i = 0 To UBound(strArrTmp) - 1
            DoEvents

            If strArrTmp(i) <> "" Then
                
                strRet = strRet & _
                         IIf(strRet = "", "", strEspacador) & _
                         strArrTmp(i)
            
            End If
        Next i
    End If

    StringPreparar_Etapa_02 = strRet

End Function
Private Function StringPreparar_Etapa_02_Regex(strColuna As String, _
                                               lngLinha As Long, _
                                               strEspacador As String) As String

    Dim i           As Long
    Dim strArrTmp() As String
    Dim strTmp      As String
    Dim strRet      As String

    strTmp = Range(strColuna & lngLinha).Value & "|"

    If strTmp <> "" And _
    strTmp <> "|" Then
        Erase strArrTmp
        strArrTmp() = Split(strTmp, "|")

        For i = 0 To UBound(strArrTmp) - 1
            DoEvents

            If strArrTmp(i) <> "" Then
                strRet = strRet & _
                         IIf(strRet = "", "", strEspacador) & _
                         ".*" & StringPreparar_Etapa_02_Regex_Acentos(strArrTmp(i)) & ".*"
            End If
        Next i
    End If

    StringPreparar_Etapa_02_Regex = strRet

End Function

Private Function StringPreparar_Etapa_02_Regex_Acentos(strConteudo As String) As String

    Dim strRet As String

    strRet = strConteudo

    strRet = Replace(strRet, "A", "[AÀÁÂÃÄÅ]")
    strRet = Replace(strRet, "a", "[aàáâãäå]")
    strRet = Replace(strRet, "E", "[EÈÉÊË]")
    strRet = Replace(strRet, "e", "[eèéêë]")
    strRet = Replace(strRet, "I", "[IÌÍÎÏ]")
    strRet = Replace(strRet, "i", "[iìíîï]")
    strRet = Replace(strRet, "O", "[OÒÓÔÕÖ]")
    strRet = Replace(strRet, "o", "[oòóôõö]")
    strRet = Replace(strRet, "U", "[UÙÚÛÜ]")
    strRet = Replace(strRet, "u", "[uùúûü]")
    strRet = Replace(strRet, "C", "[CÇ]")
    strRet = Replace(strRet, "c", "[cç]")

    StringPreparar_Etapa_02_Regex_Acentos = strRet

End Function
Private Function StringPreparar_Etapa_01_Regex(strColuna As String, _
                                               lngLinha As Long, _
                                               strEspacador As String) As String

    Dim i       As Long
    Dim strTmp  As String
    Dim strRet  As String

    i = lngLinha
    strRet = ""

    Do While UCase(Range("B" & i)) <> "FIM"
        DoEvents

        Range("A" & i).Select

        strTmp = StringPreparar_Etapa_02_Regex(strColuna, i, strEspacador)

        If strTmp <> "" Then
            strRet = strRet & _
                     IIf(strRet = "", "", vbCrLf) & _
                     Range("D" & i) & _
                     " (" & Range("E" & i) & ")" & vbCrLf & _
                     "(?i)<nome.*>(" & strTmp & ")<" & _
                     vbCrLf
        End If

        i = i + 1
    Loop

    StringPreparar_Etapa_01_Regex = strRet

End Function

'Creating custom function for copying
Function VBA_Copy_to_Clipboard(Optional StoreText As String) As String

    'Declaring variable
    Dim M As Variant

    'Storing variable as variant
    M = StoreText

    'Create HTMLFile Object
    With CreateObject("htmlfile")
        With .parentWindow.clipboardData
    
        'Deciding case for copying
            Select Case True
                'Returning the number of characters using the len function
                Case Len(StoreText)
                    'Writing to the clipboard
                    .setData "text", M
                'If there is no variable
                Case Else
                    'Reading from the clipboard and no variable passed through
                    VBA_Copy_to_Clipboard = .GetData("text")
            End Select
        End With
    End With

End Function
