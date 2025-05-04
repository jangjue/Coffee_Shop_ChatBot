import { Text, View } from 'react-native'
import React from 'react'
import { heightPercentageToDP } from 'react-native-responsive-screen';
import { MessageInterface } from '@/types/types';

interface Message {
    message: MessageInterface;
}

const MessageItem = ({message}:Message) => {
  // Add validation to ensure message content exists and is not empty
  const messageContent = message?.content || 'No message content';
  
  // Add logging to debug message content
  console.log('Rendering message:', {
    role: message?.role,
    contentLength: messageContent.length,
    contentPreview: messageContent.substring(0, 30)
  });
  
  if (message?.role === 'user') {
    return (
        <View
            className='flex-row justify-end mb-3 mr-3'
        >
            {/* Removed intermediate View. Apply maxWidth and self-end directly to the bubble */}
            <View style={{ maxWidth: '80%' }} className='self-end p-3 rounded-2xl bg-white border border-neutral-200'>
                <Text
                    style = {{fontSize: heightPercentageToDP(1.9)}}>
                    {messageContent}
                </Text>
            </View>
        </View>
    )
  } else {
    return (
        <View
            className='w-[80%] ml-3 mb-3'
        >
            <View style={{ maxWidth: '100%' }} className='flex self-start p-3 px-4 rounded-2xl bg-indigo-100 border border-indigo-200'>
                <Text
                    style = {{fontSize: heightPercentageToDP(1.9)}}
                >
                    {messageContent}
                </Text>
            </View>
        </View>
    )
  }
}

export default MessageItem