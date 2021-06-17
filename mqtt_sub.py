
# This shows a simple example of an MQTT subscriber.
import struct
import paho.mqtt.client as mqtt


def on_connect(mqttc, obj, flags, rc):
    print("rc: " + str(rc))
    mqttc.subscribe("test/topic")

def on_message(mqttc, obj, msg):
    data_length = 61
    #print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    data_tuple = struct.unpack('%sf' % data_length, msg.payload)
    r_dy_m_vec = data_tuple[0:4]
    print('r_dy_m_vec: ', r_dy_m_vec)
    k_korr_r_dyn_abs_HA_vec = data_tuple[4:9]
    print('k_korr_r_dyn_abs_HA_vec: ', k_korr_r_dyn_abs_HA_vec)
    r_dyn_1_m_vec = data_tuple[9:14]
    print('r_dyn_1_m_vec: ', r_dyn_1_m_vec)
    r_dyn_2_m_vec = data_tuple[14:19]
    print('r_dyn_2_m_vec: ', r_dyn_2_m_vec)
    r_dyn_3_m_vec = data_tuple[19:24]
    print('r_dyn_3_m_vec: ', r_dyn_3_m_vec)
    r_dyn_4_m_vec = data_tuple[24:29]
    print('r_dyn_4_m_vec: ', r_dyn_4_m_vec)
    k_korr_r_dyn_Fz = data_tuple[29]
    print('k_korr_r_dyn_Fz: ', k_korr_r_dyn_Fz)
    EKFx2_Cx_VL = data_tuple[30]
    print('EKFx2_Cx_VL: ', EKFx2_Cx_VL)
    EKFx2_Cx_VR = data_tuple[31]
    print('EKFx2_Cx_VR: ', EKFx2_Cx_VR)
    EKFx2_mue_VL = data_tuple[32]
    print('EKFx2_mue_VL: ', EKFx2_mue_VL)
    EKFx2_mue_VR = data_tuple[33]
    print('EKFx2_mue_VR: ', EKFx2_mue_VR)
    RDK_druck_bar_korr = data_tuple[34:38]
    print('RDK_druck_bar_korr: ', RDK_druck_bar_korr)
    RDK_temp_degC_korr = data_tuple[38:42]
    print('RDK_temp_degC_korr: ', RDK_temp_degC_korr)
    RDK_RadID_korr = data_tuple[42:46]
    print('RDK_RadID_korr: ', RDK_RadID_korr)
    EST_vref_HA_mps = data_tuple[46]
    print('EST_vref_HA_mps: ', EST_vref_HA_mps)
    m_ges_tires_kg_vec = data_tuple[47:51]
    print('m_ges_tires_kg_vec: ', m_ges_tires_kg_vec)
    KBI_kilometerstand = data_tuple[51]
    print('KBI_kilometerstand: ', KBI_kilometerstand)
    KBI_Aussen_temp_gef = data_tuple[52]
    print('KBI_Aussen_temp_gef: ', KBI_Aussen_temp_gef)
    TWE_Cx_HL = data_tuple[53]
    print('TWE_Cx_HL: ', TWE_Cx_HL)
    TWE_Cx_HR = data_tuple[54]
    print('TWE_Cx_HR: ', TWE_Cx_HR)
    TWE_mue_HL = data_tuple[55]
    print('TWE_mue_HL: ', TWE_mue_HL)
    TWE_mue_HR = data_tuple[56]
    print('TWE_mue_HR: ', TWE_mue_HR)
    TWE_f_eig_vec = data_tuple[57:61]
    print('TWE_f_eig_vec: ', TWE_f_eig_vec)
    print('====================================================')

def on_publish(mqttc, obj, mid):
    print("mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    print(string)


# If you want to use a specific client id, use
# mqttc = mqtt.Client("client-id")
# but note that the client id must be unique on the broker. Leaving the client
# id parameter empty will generate a random id for you.
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
# Uncomment to enable debug messages
# mqttc.on_log = on_log
mqttc.tls_set('/etc/mosquitto/ca_certificates/ca.crt')
mqttc.tls_insecure_set(True)
mqttc.connect("127.0.0.1", 8883)

mqttc.loop_forever()
