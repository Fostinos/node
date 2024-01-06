#include <stdint.h>
#include <stdbool.h>
#include <string.h> // for memcpy
#include "lw_crypto.h"
#include "lw_base64.h"
#include "lorawan.h"



static uint16_t parseUInt16LittleEndian(const uint8_t *bytes);
static uint32_t parseUInt32LittleEndian(const uint8_t *bytes);
static void convertInPlaceEUI64bufLittleEndian(uint8_t *eui8buf);

static uint8_t LoRaWAN_DataUp(MACPayload_t * packet, uint8_t* buffer, uint8_t bufferSize, bool isConfirmed);

MHDR_MType_t LoRaWAN_MessageType(uint8_t* buffer, uint8_t bufferSize)
{
    if(bufferSize < 1)
    {
        return MTYPE_PROPRIETARY;
    }
    return ((MHDR_MType_t)(buffer[0] >> 5));

}

uint8_t LoRaWAN_JoinRequest(JoinRequest_t * packet, uint8_t* buffer, uint8_t bufferSize)
{
    uint8_t index = 0;
    lw_mic_t mic;     	// 4 byte lorawan message integrity code (last bytes of PHYPayload)
    lw_key_t lw_key; 	// lorawan AES de/encrypt input struct (see crypto.c for details)

    if(bufferSize < 4)
    {
        return index;
    }
    // MHDR
    buffer[index++] = (MTYPE_JOIN_REQUEST << 5) | (LORAWAN_R1);

    if(bufferSize < index + 8)
    {
        return 0;
    }
    memcpy(buffer + index, packet->AppEUI, 8);
    convertInPlaceEUI64bufLittleEndian(buffer + index);
    index += 8;

    if(bufferSize < index + 8)
    {
        return 0;
    }
    memcpy(buffer + index, packet->DevEUI, 8);
    convertInPlaceEUI64bufLittleEndian(buffer + index);
    index += 8;

    if(bufferSize < index + 2)
    {
        return 0;
    }
    buffer[index++] = (uint8_t) (packet->DevNonce & 0xffu);
    buffer[index++] = (uint8_t) (packet->DevNonce >> 8u);

    lw_key.AESkey = packet->AppKey;
    lw_key.in = buffer;
    lw_key.len = index;
    lw_join_mic(&mic, &lw_key);

    if (bufferSize < index + 4) {
        return 0;
    }
    memcpy(buffer + index, mic.buf, 4);
    index += 4;
    return index;
}

bool LoRaWAN_JoinAccept(JoinAccept_t * packet, uint8_t* buffer, uint8_t bufferSize)
{
    uint8_t index;
    lw_mic_t mic;        // calculated mic
    lw_key_t lw_key;

    // MHDR(1) + [sizeof(JoinAccept_t)(12) + optional CFlist(16)] + MIC(4), max len: 33 byte
    if(bufferSize == 17)
    {
        packet->hasCFlist = false;
    }else if(bufferSize == 17 + 16)
    {
        packet->hasCFlist = true; // optional frequency list send by network server
    }else
    {
        return false;
    }

    // (1) beside MHDR whole the message is encrypted -> decrypt it first
    uint8_t decryptedBuffer[33];    // temp buffer
    lw_key.AESkey = packet->AppKey;  
    lw_key.in = buffer + 1;         // skip MHDR
    lw_key.len = bufferSize - 1;
    decryptedBuffer[0] = buffer[0]; // MHDR can be copied as it's not encrypted
    int len = lw_join_decrypt(decryptedBuffer + 1, &lw_key);


    if(len <= 0)
    {
        return false;
    }

    // Check MIC
    uint32_t receivedMIC = parseUInt32LittleEndian(decryptedBuffer + bufferSize - 4);
    

    lw_key.AESkey = packet->AppKey;
    lw_key.in = decryptedBuffer;
    lw_key.len = bufferSize - 4;    // skip MIC
    lw_join_mic(&mic, &lw_key);
    
    if(mic.data != receivedMIC)     // check if mic is ok
    {   
        return false;
    }

    // Parse fields
    index = 1; // skip already parsed MHDR
    packet->AppNonce = decryptedBuffer[index++];
    packet->AppNonce |= ((uint32_t) decryptedBuffer[index++] << 8);
    packet->AppNonce |= ((uint32_t) decryptedBuffer[index++] << 16);

    packet->NetID = decryptedBuffer[index++];
    packet->NetID |= ((uint32_t) decryptedBuffer[index++] << 8);
    packet->NetID |= ((uint32_t) decryptedBuffer[index++] << 16);

    packet->DevAddr = parseUInt32LittleEndian(&(decryptedBuffer[index]));
    index += 4;
    packet->DLsettings.OptNeg = ((decryptedBuffer[index] & 0x80) >> 7);
    packet->DLsettings.Rx1DRoffset = ((decryptedBuffer[index] & 0x70) >> 4);
    packet->DLsettings.Rx2DR = (decryptedBuffer[index] & 0x0F);
    index++;

    packet->RxDelay = decryptedBuffer[index++];

    if(packet->hasCFlist)
    {
        memcpy(packet->CFlist.FreqCH4, decryptedBuffer + index, 3);
        memcpy(packet->CFlist.FreqCH5, decryptedBuffer + index + 3, 3);
        memcpy(packet->CFlist.FreqCH6, decryptedBuffer + index + 6, 3);
        memcpy(packet->CFlist.FreqCH7, decryptedBuffer + index + 9, 3);
        memcpy(packet->CFlist.FreqCH8, decryptedBuffer + index + 12, 3);
    }

    lw_skey_seed_t lw_skey_seed;
    lw_skey_seed.AESkey = packet->AppKey;
    lw_skey_seed.anonce.data = packet->AppNonce;
    lw_skey_seed.netid.data = packet->NetID;
    lw_skey_seed.dnonce.data = packet->DevNonce;
    lw_get_skeys(packet->NwkSKey, packet->AppSKey, &lw_skey_seed); 

    return true;
}

uint8_t LoRaWAN_UnconfirmedDataUp(MACPayload_t * packet, uint8_t* buffer, uint8_t bufferSize)
{
    return LoRaWAN_DataUp(packet, buffer, bufferSize, false);
}

uint8_t LoRaWAN_ConfirmedDataUp(MACPayload_t * packet, uint8_t* buffer, uint8_t bufferSize)
{
    return LoRaWAN_DataUp(packet, buffer, bufferSize, true);
}

bool LoRaWAN_DataDown(MACPayload_t * packet, uint8_t* buffer, uint8_t bufferSize)
{
    uint8_t index;
    lw_mic_t mic;        // calculated mic
    lw_key_t lw_key;

    // skip MHDR
    index = 1; 
    // No FPort, no payload at the beginning
    packet->FPort = 0;
    packet->payloadSize = 0;

    // get DevAddr since we need it for MIC check
    uint32_t DevAddr = parseUInt32LittleEndian(&buffer[index]);
    index += 4;
    if(packet->FHDR.DevAddr != DevAddr) 
    {
        return false;
    }

    if(bufferSize - 4 < index + 3)
    {
        return false;
    }
    // MHDR(1) + DevAddr(4) + FCtrl(1) + FCnt(2) + FOpts(foptslen) + FPort(1)
    uint8_t FCtrl = buffer[index];
    index++;
    packet->FHDR.FCnt16 = parseUInt16LittleEndian(&buffer[index]);
    index += 2;
    packet->FHDR.FCtrl.downlink.ADR = FCtrl >> 7;
    packet->FHDR.FCtrl.downlink.ACK = (FCtrl & (0x01 << 5)) >> 5;
    packet->FHDR.FCtrl.downlink.FPending = (FCtrl & (0x01 << 4)) >> 4;
    packet->FHDR.FCtrl.downlink.FOptsLen = (FCtrl & 0x0F);
    
    lw_key.in = buffer;
    lw_key.len = bufferSize - 4;
    lw_key.devaddr.data = packet->FHDR.DevAddr;
    lw_key.fcnt32 = packet->FHDR.FCnt16;
    lw_key.link = LW_DOWNLINK;
    // calculate & compare mic
    uint32_t receivedMIC = parseUInt32LittleEndian(&buffer[bufferSize - 4]);
    lw_key.AESkey = packet->NwkSKey;
    lw_msg_mic(&mic, &lw_key);
    if(mic.data != receivedMIC)
    {
        return false;
    }
    memcpy(packet->FHDR.FOpts, &buffer[index], packet->FHDR.FCtrl.downlink.FOptsLen);
    index += packet->FHDR.FCtrl.downlink.FOptsLen;

    if(bufferSize - 4 < index + 1)
    {
        // No FPort, no payload
        return true;
    }
    packet->FPort = buffer[index];
    index++;
	
    if(bufferSize - 4 < index + 1)
    {
        // No Payload
        return true;
    }
    // Calculate payloadSize
    packet->payloadSize = bufferSize - 4 - index;

    lw_key.AESkey = packet->AppSKey;
    lw_key.in = &buffer[index];
    lw_key.len = packet->payloadSize;

    // decrypt by encrypt
    if(lw_encrypt(packet->payload, &lw_key) <= 0)
    {
        // No payload decrypted
        return false;
    }

    return true;
}

uint32_t LoRaWAN_Base64_To_Binary(const char * in, int size, uint8_t * out, int max_len)
{
    size = b64_to_bin(in, size, out, max_len);
    if(size <= 0)
    {
        return 0;
    }
    return size;
}

uint32_t LoRaWAN_Binary_To_Base64(const uint8_t * in, int size, char * out, int max_len)
{
    size = bin_to_b64(in, size, out, max_len);
    if(size <= 0)
    {
        return 0;
    }
    return size;
} 


static uint8_t LoRaWAN_DataUp(MACPayload_t * packet, uint8_t* buffer, uint8_t bufferSize, bool isConfirmed)
{
    uint8_t index = 0;
    lw_mic_t mic;
    lw_key_t lw_key;

    if(bufferSize < 4)
    {
        return index;
    }

    // MHDR
    if(isConfirmed)
    {
        buffer[index++] = (MTYPE_CONFIRMED_DATA_UP << 5) | (LORAWAN_R1);
    }else
    {
        buffer[index++] = (MTYPE_UNCONFIRMED_DATA_UP << 5) | (LORAWAN_R1);
    }

    // FHDR
    if (bufferSize < index + 4) {
        return 0;
    }
    buffer[index++] = (uint8_t) (packet->FHDR.DevAddr & 0xFF);
    buffer[index++] = (uint8_t) (packet->FHDR.DevAddr >> 8);
    buffer[index++] = (uint8_t) (packet->FHDR.DevAddr >> 16);
    buffer[index++] = (uint8_t) (packet->FHDR.DevAddr >> 24);
    lw_key.devaddr.data = packet->FHDR.DevAddr;

    // Uplink packet
    lw_key.link = LW_UPLINK;
    if(bufferSize < index + 1)
    {
        return 0;
    }
    buffer[index++] = (packet->FHDR.FCtrl.uplink.ADR << 7)
                        | (packet->FHDR.FCtrl.uplink.ADRACKReq << 6)
                        | (packet->FHDR.FCtrl.uplink.ACK << 5)
                        | (packet->FHDR.FCtrl.uplink.FOptsLen);

    
    if(bufferSize < index + 2)
    {
        return 0;
    }
    // Little endian
    buffer[index++] = (uint8_t) (packet->FHDR.FCnt16 & 0xFF);
    buffer[index++] = (uint8_t) (packet->FHDR.FCnt16 >> 8);
    lw_key.fcnt32 = packet->FHDR.FCnt16;

    // Encrypt payload (if present and FPort > 0)
    if (packet->payloadSize != 0 && packet->FPort != 0)
    {
        if(bufferSize < index + 1)
        {
            return 0;
        }
        buffer[index++] = packet->FPort;
        lw_key.AESkey = packet->AppSKey;
        lw_key.in = packet->payload;
        lw_key.len = packet->payloadSize;

        int cryptedPayloadSize = lw_encrypt(buffer + index, &lw_key);
        index += cryptedPayloadSize;
        if(bufferSize < index)
        {
            return 0;
        }
    }

    // 4 byte MIC
    if (bufferSize < index + 4)
    {
        return 0;
    }

    lw_key.AESkey = packet->NwkSKey;
    lw_key.in = buffer;
    lw_key.len = index;
    lw_msg_mic(&mic, &lw_key);
    memcpy(buffer + index, mic.buf, 4);
    index += 4;

    return index; 
}



static uint16_t parseUInt16LittleEndian(const uint8_t *bytes) {
    return (((uint16_t) bytes[0]) << 0u) | (((uint16_t) bytes[1]) << 8u);
}

static uint32_t parseUInt32LittleEndian(const uint8_t *bytes) {
    return (((uint32_t) bytes[0]) << 0u) | (((uint32_t) bytes[1]) << 8u) | (((uint32_t) bytes[2]) << 16u) | (((uint32_t) bytes[3]) << 24u);
}

static void convertInPlaceEUI64bufLittleEndian(uint8_t *eui8buf) {
    uint8_t tmp[8];
    if (eui8buf) {
        memcpy(tmp, eui8buf, 8);
        for (int i = 0; i < 8; i++) {
            eui8buf[i] = tmp[7 - i];
        }
    }
}
