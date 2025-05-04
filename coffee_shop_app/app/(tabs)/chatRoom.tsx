import { Alert, TouchableOpacity, View, Text, ToastAndroid, Platform } from 'react-native';
import React, { useEffect, useRef, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import MessageList from '@/components/MessageList';
import { MessageInterface } from '@/types/types';
import { widthPercentageToDP as wp, heightPercentageToDP as hp } from 'react-native-responsive-screen';
import { GestureHandlerRootView, TextInput } from 'react-native-gesture-handler';
import { Feather } from '@expo/vector-icons';
import { callChatBotAPI } from '@/services/chatBot';
import PageHeader from '@/components/PageHeader';
import { useCart } from '@/components/CartContext';
import { getCachedMenuItems } from '@/services/productService';

const ChatRoom = () => {
    const { addToCart, emptyCart } = useCart();
    const [currentOrder, setCurrentOrder] = useState<any[]>([]);
    const [messages, setMessages] = useState<MessageInterface[]>([
        {
            role: 'assistant',
            content: "Hello! Welcome to Old Kasturi Coffee. How can I help you today? Feel free to ask for recommendations, place an order, or inquire about our menu. \n\nFor example:\n- 'What drinks do you recommend?'\n- 'I'd like to order a Cappuccino and a Croissant.'\n- 'Tell me about your pastries.'"
        }
    ]);
    const [isTyping, setIsTyping] = useState<boolean>(false);
    const [menuItems, setMenuItems] = useState<Record<string, number>>({});
    const textRef = useRef('');
    const inputRef = useRef<TextInput>(null);

    useEffect(() => {
        const loadMenuItems = async () => {
            try {
                const items = await getCachedMenuItems();
                setMenuItems(items);
                console.log('✅ Menu items loaded:', Object.keys(items).length);
            } catch (error) {
                console.error('❌ Failed to load menu items:', error);
            }
        };
        loadMenuItems();
    }, []);

    const showFeedback = (message: string) => {
        if (Platform.OS === 'android') {
            ToastAndroid.show(message, ToastAndroid.SHORT);
        } else {
            Alert.alert('Order Update', message);
        }
    };

    // Removed extractItemsFromText function

    const ordersAreDifferent = (newOrder: any[], oldOrder: any[]): boolean => {
        if (!newOrder || !oldOrder) return true;
        if (newOrder.length !== oldOrder.length) return true;

        // Create normalized maps of items to their quantities for both orders
        const newOrderMap: Record<string, number> = {};
        const oldOrderMap: Record<string, number> = {};
        
        // Normalize item names to lowercase for case-insensitive comparison
        newOrder.forEach(item => {
            const normalizedName = item.item.toLowerCase();
            newOrderMap[normalizedName] = Number(item.quantity);
        });
        
        oldOrder.forEach(item => {
            const normalizedName = item.item.toLowerCase();
            oldOrderMap[normalizedName] = Number(item.quantity);
        });
        
        // Compare normalized maps
        const allKeys = new Set([...Object.keys(newOrderMap), ...Object.keys(oldOrderMap)]);
        for (const key of allKeys) {
            if (newOrderMap[key] !== oldOrderMap[key]) {
                console.log(`Order difference detected: ${key} - New: ${newOrderMap[key]}, Old: ${oldOrderMap[key]}`);
                return true;
            }
        }

        return false;
    };

    // Removed extractItemsFromUserMessage function
    // Removed findMatchingMenuItem function

    const handleSendMessage = async () => {
        let message = textRef.current.trim();
        if (!message) return;

        try {
            // Removed client-side item extraction
            let InputMessages = [...messages, { content: message, role: 'user' }];
            setMessages(InputMessages);
            textRef.current = '';
            inputRef?.current?.clear();
            setIsTyping(true);

            let responseMessage = await callChatBotAPI(InputMessages);
            setIsTyping(false);
            setMessages(prev => [...prev, responseMessage]);

            console.groupCollapsed("🤖 ChatBot Log");
            console.log("User Message:", message);
            console.log("Bot Response:", responseMessage.content);
            console.groupEnd();

            if (responseMessage && responseMessage.memory) {
                const orderItems = responseMessage.memory.order;

                if (Array.isArray(orderItems) && orderItems.length > 0) {
                    if (ordersAreDifferent(orderItems, currentOrder)) {
                        const newItems = orderItems.filter(newItem =>
                            !currentOrder.some(oldItem =>
                                oldItem.item === newItem.item &&
                                Number(oldItem.quantity) === Number(newItem.quantity)
                            )
                        );

                        setCurrentOrder(orderItems);
                        emptyCart();
                        orderItems.forEach((item: any) => {
                            if (item && item.item) {
                                const quantity = Number(item.quantity || 1);
                                addToCart(item.item, quantity);
                            }
                        });

                        if (newItems.length > 0) {
                            const itemText = newItems.map(i => `${i.quantity} ${i.item}`).join(", ");
                            showFeedback(`Added to cart: ${itemText}`);
                        }
                    }
                }
                // Removed fallback logic based on client-side extraction
            }
        } catch (err: any) {
            console.error("❌ Chat processing error:", err);
            Alert.alert('Error', err.message);
        }
    };

    return (
        <GestureHandlerRootView>
            <StatusBar style='dark' />
            <View className='flex-1 bg-white'>
                <PageHeader title="Chat Bot" showHeaderRight={false} bgColor='white' />
                <View className='h-3 border-b border-neutral-300' />
                <View className='flex-1 justify-between bg-neutral-100 overflow-visibile'>
                    <View className='flex-1'>
                        <MessageList messages={messages} isTyping={isTyping} />
                    </View>
                    <View style={{ marginBottom: hp(2.7) }} className='pt-2'>
                        <View className="flex-row mx-3 justify-between border p-2 bg-white border-neutral-300 rounded-full pl-5">
                            <TextInput
                                ref={inputRef}
                                onChangeText={value => textRef.current = value}
                                placeholder='Type message...'
                                style={{ fontSize: hp(2) }}
                                className='flex-1 mr2'
                            />
                            <TouchableOpacity
                                onPress={handleSendMessage}
                                className='bg-neutral-200 p-2 mr-[1px] rounded-full'
                            >
                                <Feather name="send" size={hp(2.7)} color="#737373" />
                            </TouchableOpacity>
                        </View>
                    </View>
                </View>
            </View>
        </GestureHandlerRootView>
    );
};

export default ChatRoom;
