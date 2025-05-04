import { Text, View,TouchableOpacity, ScrollView, StatusBar  } from 'react-native'
import React, { useState } from 'react'
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { router } from 'expo-router'
import { useLocalSearchParams } from "expo-router";
import PageHeader from '@/components/PageHeader';
import { useCart } from '@/components/CartContext';
import Toast from 'react-native-root-toast';
import DescriptionSection from '@/components/DescriptionSection';
import SizesSection from '@/components/SizesSection';
import DetailsHeader from '@/components/DetailsHeader';

const DetailsPage = () => {
  const { addToCart } = useCart();
  const [quantity, setQuantity] = useState(1);

  const { name, image_url, type, description, price, rating } = useLocalSearchParams() as { name: string, image_url: string, type: string, description: string, price: string, rating: string };
  
  const buyNow = () => {
    addToCart(name, quantity);
    Toast.show(`${name} added to cart`, {
      duration: Toast.durations.SHORT,
    });
    router.back();
  };

  const increaseQuantity = () => {
    setQuantity(prev => prev + 1);
  };

  const decreaseQuantity = () => {
    if (quantity > 1) {
      setQuantity(prev => prev - 1);
    }
  };

  return (
    <GestureHandlerRootView
      className='bg-[#F9F9F9] w-full h-full'
    >
      <StatusBar backgroundColor="white" />

      <PageHeader title="Detail" showHeaderRight={true} bgColor='#F9F9F9' />
      
      <View className='h-full flex-col justify-between'>
        <ScrollView>
            <View className='mx-5 items-center'>
              <DetailsHeader image_url={image_url} name={name} type={type} rating={Number(rating)} />
              <DescriptionSection description={description} />
              <SizesSection />
              
              {/* Quantity Selector */}
              <View className="w-full mt-4">
                <Text className="text-lg font-[Sora-SemiBold] text-[#242424] mb-2">Quantity</Text>
                <View className="flex-row items-center justify-between bg-white p-3 rounded-lg">
                  <TouchableOpacity 
                    onPress={decreaseQuantity}
                    className="bg-[#F4F4F4] w-10 h-10 rounded-full items-center justify-center"
                  >
                    <Text className="text-xl font-semibold">-</Text>
                  </TouchableOpacity>
                  
                  <Text className="text-xl font-[Sora-Medium]">{quantity}</Text>
                  
                  <TouchableOpacity 
                    onPress={increaseQuantity}
                    className="bg-[#F4F4F4] w-10 h-10 rounded-full items-center justify-center"
                  >
                    <Text className="text-xl font-semibold">+</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>
        </ScrollView>
        
        <View
          className='flex-row justify-between bg-white rounded-tl-3xl rounded-tr-3xl px-6 pt-3 pb-6'
        > 
          <View>
            <Text
                    className="text-[#A2A2A2] text-base font-[Sora-Regular] pb-3"
              >Price
            </Text>
            <Text
                    className="text-app_orange_color text-2xl font-[Sora-SemiBold]"
              >RM {(Number(price) * quantity).toFixed(2)}
            </Text>
          </View>
            
          <TouchableOpacity 
                className="bg-app_orange_color w-[70%] rounded-3xl items-center justify-center" 
                onPress={buyNow}
              >
                <Text className="text-xl color-white font-[Sora-Regular]">Buy Now</Text> 
          </TouchableOpacity> 
        
        </View>
        
      </View>
      
        
    </GestureHandlerRootView>
  )
}

export default DetailsPage