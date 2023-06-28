if [[ -z $DEBUG ]]; then
    DEBUG=true
fi

if [[ -z $REMOTE ]]; then
    REMOTE=false
fi


#デバッグモードかリリースモードか
if $DEBUG ; then
    echo "DEBUG MODE"
    DEBUG=true
else
    echo "RELEASE MODE"
    DEBUG=false
fi

#リモート設定かローカル設定か
if $REMOTE; then
    echo "REMOTE MODE"
    PORT=10001
    IP="160.16.83.206"
else
    echo "LOCAL MODE"
    PORT=10000
    IP="localhost"
fi

# NUM_AGENT分のエージェントを起動
NUM_AGENT=5

for i in `seq 1 $NUM_AGENT`
do
    echo "start agent_$i"
    #リリースとデバッグでエージェントを切り替える
    if $DEBUG ; then
        python3 aiwolfk2b/AttentionReasoningAgent/SimpleAttentionReasoningAgent.py -p $PORT -h $IP -n "python_agent_${i}" &
        # python3 aiwolfk2b/agentLPS/python_simple_protocol_agent.py -p $PORT -h $IP -n "python_agent_${i}" &
    else
        python3 aiwolfk2b/agentLPS/protocol_wrapper_agent.py -p $PORT -h $IP -n "python_agent_${i}" &
    fi
done

wait