import discord
import os
import threading
import gradio as gr
import requests
import json
import random
import time
import re
from discord import Embed, Color
from discord.ext import commands
# test # fix? # unstick # fix
from gradio_client import Client
from PIL import Image
#from ratelimiter import RateLimiter

import asyncio
import concurrent.futures
import multiprocessing

import shutil # for doing image movement magic

#todo
# add safetychecks to all parts, test thoroughly
# add discord channels, configure for fellows
# add debugging messages, same as in deepfloydif, to the_painter
# experiment with animeGANv2

#✅ 4 -> combined image
# loading emoji? animated emojis?
# make success / fail emojis more consistent across both painter + dfif
#✅ tasks for concurrent coroutines
# ratelimits

# enlarge each of 4 images?
# Error: [Errno 104] Connection reset by peer?

# clean up old threads
# safety for on_reaction_add?
# could use one channel, use threads to organize it. Otherwise may be too split and harder to keep track of
# lock generation after ~120s, can change
# restructure using slash commands? generate -> deepfloydif -> prompt -> thread -> combined -> upscale -> thread

GRADIOTEST_TOKEN = os.getenv('HF_TOKEN')
DISCORD_TOKEN = os.environ.get("GRADIOTEST_TOKEN", None)

df = Client("huggingface-projects/IF", GRADIOTEST_TOKEN)
jojogan = Client("akhaliq/JoJoGAN", GRADIOTEST_TOKEN)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)


#---------------------------------------------------------------------------------------------------------------------------------------------
@bot.event
async def on_ready():
    print('Logged on as', bot.user)
    bot.log_channel = bot.get_channel(1100458786826747945) # 1100458786826747945 = bot-test, 1107006391547342910 = lunarbot server  
#--------------------------------------------------------------------------------------------------------------------------------------------- 
@bot.command()
async def commands(ctx):
    try:
        if await safetychecks(ctx):    
            await ctx.reply(f"Use !jojo !disney !spidey or !sketch. Have fun! 🤗💖")
    except Exception as e:
        print(f"Error: unable to help :(")   
#---------------------------------------------------------------------------------------------------------------------------------------------   
async def safetychecks(ctx):
    try:
        if ctx.author.bot:
            print(f"Error: The bot is not allowed to use its own commands.")
            return False
    
        #✅✅ check if the bot is offline 
        offline_bot_role_id = 1103676632667017266
        bot_member = ctx.guild.get_member(bot.user.id)
        if any(role.id == offline_bot_role_id for role in bot_member.roles):
            print(f"Error: The bot is offline or under maintenance. (Remove the offline-bot role to bring it online)")         
            return False
        else:
            await ctx.reply(f"✅{bot} is online")            
    
        #✅✅ check if the command is in the allowed channel(s)
        channel_id = 1100458786826747945
        if ctx.channel.id != channel_id: # #bot-test = 1100458786826747945
            print(f"If using a command, commands are not permitted in {ctx.channel}")
            return False
        else:
            await ctx.reply(f"✅{ctx.channel} is a valid channel for commands")            
            
        #✅✅ check if the user has the required role(s)   
        guild_id = 879548962464493619
        required_role_id = 900063512829755413  # @verified = 900063512829755413,  HF = 897376942817419265
        guild = bot.get_guild(guild_id)
        required_role = guild.get_role(required_role_id)
        if required_role not in ctx.author.roles:
            print(f"Error: The user does not have the required role to use that command. ({required_role} is the correct role)")        
            return False
        else:
            await ctx.reply(f"✅{ctx.author} has the required role {required_role}")
    
        return True

    # ping lunarflu if any safety check ever fails
    except Exception as e:
        print(f"Error: safetychecks failed somewhere, command will not continue.")
        await ctx.message.reply(f"❌ <@811235357663297546> SC failed somewhere ❌") # this will always ping, as long as the bot has access to the channel
#---------------------------------------------------------------------------------------------------------------------------------------------- 
# jojo ✅
@bot.command()
async def jojo(ctx):
    # img + face    ✅
    # img + no face ✅
    # no image      ✅
    # no generation ✅
    # responsive?   ✅
    # ratelimits?   ❌
    # safety checks?✅
    # bot no crash  ✅
    try:  
        if await safetychecks(ctx): #✅
            await ctx.message.add_reaction('🤖') 
            thread = await ctx.message.create_thread(name=f'{ctx.author} Jojo Thread')         
            if ctx.message.attachments:
                await thread.send(f'{ctx.author.mention}Generating images in thread, can take ~1 minute...yare yare, daze ...')  
                attachment = ctx.message.attachments[0]
                style = 'JoJo'
                #im = jojogan.predict(attachment.url, style)
                im = await asyncio.get_running_loop().run_in_executor(None, jojogan.predict, attachment.url, style)
                #await ctx.message.reply(f'Here is the {style} version of it', file=discord.File(im))
                await thread.send(f'{ctx.author.mention}Here is the {style} version of it', file=discord.File(im))
                await ctx.message.add_reaction('✅') # img + face    
            else: # no image
                await thread.send(f"{ctx.author.mention}No attachments to be found...Can't animify dat! Try sending me an image 😉")
                await ctx.message.add_reaction('❌')             
    except Exception as e: # no generation / img + no face
        print(f"Error: {e}")
        await thread.send(f"{ctx.author.mention}Error: {e}")
        await ctx.message.add_reaction('❌')            
        
#---------------------------------------------------------------------------------------------------------------------------------------------- 
# Disney ❌
@bot.command()
async def disney(ctx):
    try:
        if await safetychecks(ctx): #✅
            await ctx.message.add_reaction('🤖') 
            thread = await ctx.message.create_thread(name=f'{ctx.author} disney Thread')         
            if ctx.message.attachments:
                await thread.send(f'{ctx.author.mention}Generating images in thread, can take ~1 minute...')  
                attachment = ctx.message.attachments[0]
                style = 'disney'
                im = await asyncio.get_running_loop().run_in_executor(None, jojogan.predict, attachment.url, 'disney')
                await thread.send(f'{ctx.author.mention}Here is the {style} version of it', file=discord.File(im))
                await ctx.message.add_reaction('✅') # img + face    
            else: # no image
                await thread.send(f"{ctx.author.mention}No attachments to be found...Can't animify dat! Try sending me an image 😉")
                await ctx.message.add_reaction('❌')             
    except Exception as e: # no generation / img + no face
        print(f"Error: {e}")
        await thread.send(f"{ctx.author.mention}Error: {e}")
        await ctx.message.add_reaction('❌') 
        
#---------------------------------------------------------------------------------------------------------------------------------------------- 
# Spider-Verse ✅
@bot.command()
async def spidey(ctx):
    try:
        if await safetychecks(ctx): #✅
            await ctx.message.add_reaction('🤖') 
            thread = await ctx.message.create_thread(name=f'{ctx.author} spider-verse Thread')         
            if ctx.message.attachments:
                await thread.send(f'{ctx.author.mention}Generating images in thread, can take ~1 minute...')  
                attachment = ctx.message.attachments[0]
                style = 'Spider-Verse'
                im = await asyncio.get_running_loop().run_in_executor(None, jojogan.predict, attachment.url, style)
                await thread.send(f'{ctx.author.mention}Here is the {style} version of it', file=discord.File(im))
                await ctx.message.add_reaction('✅') # img + face    
            else: # no image
                await thread.send(f"{ctx.author.mention}No attachments to be found...Can't animify dat! Try sending me an image 😉")
                await ctx.message.add_reaction('❌')             
    except Exception as e: # no generation / img + no face
        print(f"Error: {e}")
        await thread.send(f"{ctx.author.mention}Error: {e}")
        await ctx.message.add_reaction('❌') 
        
#---------------------------------------------------------------------------------------------------------------------------------------------- 
# sketch ✅
@bot.command()
async def sketch(ctx):
    try:    
        if await safetychecks(ctx): #✅
            await ctx.message.add_reaction('🤖') 
            thread = await ctx.message.create_thread(name=f'{ctx.author} sketch Thread')         
            if ctx.message.attachments:
                await thread.send(f'{ctx.author.mention}Generating images in thread, can take ~1 minute...')  
                attachment = ctx.message.attachments[0]
                #style = 'sketch'
                im = await asyncio.get_running_loop().run_in_executor(None, jojogan.predict, attachment.url, 'sketch')
                await thread.send(f'{ctx.author.mention}Here is the sketch version of it', file=discord.File(im))
                await ctx.message.add_reaction('✅') # img + face    
            else: # no image
                await thread.send(f"{ctx.author.mention}No attachments to be found...Can't animify dat! Try sending me an image 😉")
                await ctx.message.add_reaction('❌')             
    except Exception as e: # no generation / img + no face
        print(f"Error: {e}")
        await thread.send(f"{ctx.author.mention}Error: {e}")
        await ctx.message.add_reaction('❌') 
#----------------------------------------------------------------------------------------------------------------------------------------------
# deepfloydif stage 1 generation ✅
def inference(prompt):
    negative_prompt = ''
    seed = random.randint(0, 1000)
    #seed = 1
    number_of_images = 4
    guidance_scale = 7
    custom_timesteps_1 = 'smart50'
    number_of_inference_steps = 50
    
    stage_1_results, stage_1_param_path, stage_1_result_path = df.predict(
        prompt, negative_prompt, seed, number_of_images, guidance_scale, custom_timesteps_1, number_of_inference_steps, api_name='/generate64')
    
    return [stage_1_results, stage_1_param_path, stage_1_result_path]
#---------------------------------------------------------------------------------------------------------------------------------------------- 
# deepfloydif stage 2 upscaling ❌
def inference2(index):
    selected_index_for_stage_2 = index
    seed_2 = 0
    guidance_scale_2 = 4
    custom_timesteps_2 = 'smart50'
    number_of_inference_steps_2 = 50
    result_path = df.predict(stage_1_result_path, selected_index_for_stage_2, seed_2, 
                             guidance_scale_2, custom_timesteps_2, number_of_inference_steps_2, api_name='/upscale256')
    
    return [result_path]    
#----------------------------------------------------------------------------------------------------------------------------------------------  
# ✅
async def react1234(reaction_emojis, combined_image_dfif):
    for emoji in reaction_emojis:
        await combined_image_dfif.add_reaction(emoji)  
#----------------------------------------------------------------------------------------------------------------------------------------------  
# Stage 1 ✅
@bot.command()
async def deepfloydif(ctx, *, prompt: str):
    try:
        try:
            if await safetychecks(ctx): #✅
                await ctx.message.add_reaction('🤖') # loading emoji?
                dfif_command_message_id = ctx.message.id # we will use this in some magic later on
                thread = await ctx.message.create_thread(name=f'{ctx.author} DeepfloydIF Image Upscaling Thread ')
                # create thread -> send new message inside thread + combined_image -> add reactions -> dfif2
    
                #current_time = int(time.time())
                #random.seed(current_time)
    
                negative_prompt = ''
                seed = random.randint(0, 1000)
                #seed = 1
                number_of_images = 4
                guidance_scale = 7
                custom_timesteps_1 = 'smart50'
                number_of_inference_steps = 50
                api_name = '/generate64'
    
                await thread.send(f'✅{ctx.author.mention}Generating images in thread, can take ~1 minute...')
            
        except Exception as e:
            print(f"Error: {e}")
            await ctx.reply('stage 1 error -> pre generation')
            await ctx.message.add_reaction('❌')
            
        #generation✅-------------------------------------------------------
        try:
            #stage_1_results, stage_1_param_path, stage_1_result_path = df.predict(
            #    prompt, negative_prompt, seed, number_of_images, guidance_scale, custom_timesteps_1, number_of_inference_steps, api_name='/generate64')

            # run blocking function in executor
            await thread.send(f'✅running blocking function in executor')            
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, inference, prompt)
            await thread.send(f'✅run_in_executor ran successfully')            
            stage_1_results = result[0]
            stage_1_result_path = result[2]
            
            partialpath = stage_1_result_path[5:] #magic for later
            
        except Exception as e:
            print(f"Error: {e}")
            await ctx.reply('❌stage 1 error -> during generation')
            await ctx.message.add_reaction('❌')            
        #posting images✅----------------------------------------------------------------    
        try:
            await thread.send(f'✅combining images...') 
            png_files = [f for f in os.listdir(stage_1_results) if f.endswith('.png')]

            if png_files:
                first_png = png_files[0]
                second_png = png_files[1]
                third_png = png_files[2]
                fourth_png = png_files[3]
    
                first_png_path = os.path.join(stage_1_results, first_png)
                second_png_path = os.path.join(stage_1_results, second_png)
                third_png_path = os.path.join(stage_1_results, third_png)
                fourth_png_path = os.path.join(stage_1_results, fourth_png)
    
                img1 = Image.open(first_png_path)
                img2 = Image.open(second_png_path)
                img3 = Image.open(third_png_path)
                img4 = Image.open(fourth_png_path)
    
                combined_image = Image.new('RGB', (img1.width * 2, img1.height * 2))
    
                combined_image.paste(img1, (0, 0))
                combined_image.paste(img2, (img1.width, 0))
                combined_image.paste(img3, (0, img1.height))
                combined_image.paste(img4, (img1.width, img1.height))
    
                combined_image_path = os.path.join(stage_1_results, f'{partialpath}{dfif_command_message_id}.png')
                combined_image.save(combined_image_path)   

            with open(combined_image_path, 'rb') as f:
                combined_image_dfif = await thread.send(f'{ctx.author.mention}React with the image number you want to upscale!', file=discord.File(
                    f, f'{partialpath}{dfif_command_message_id}.png')) # named something like: tmpgtv4qjix1111269940599738479.png 

            await thread.send(f'✅reacting with 1234...') 
            emoji_list = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
            await react1234(emoji_list, combined_image_dfif)
            
            ''' individual images
            if png_files:
                for i, png_file in enumerate(png_files):
                    png_file_path = os.path.join(stage_1_results, png_file)
                    img = Image.open(png_file_path)
                    image_path = os.path.join(stage_1_results, f'{i+1}{partialpath}.png')
                    img.save(image_path)
                    with open(image_path, 'rb') as f:
                        await thread.send(f'{ctx.author.mention}Image {i+1}', file=discord.File(f, f'{i+1}{partialpath}.png'))
                    await asyncio.sleep(1)             
            
            '''
            
        except Exception as e:
            print(f"Error: {e}")
            await ctx.reply('❌stage 1 error -> posting images in thread')
            await ctx.message.add_reaction('❌')
            
    #deepfloydif try/except
    except Exception as e:
        print(f"Error: {e}")
        await ctx.reply('❌An error occurred in stage 1 for deepfloydif')
        await ctx.message.add_reaction('❌')

#----------------------------------------------------------------------------------------------------------------------------
# Stage 2 ✅
async def dfif2(index: int, stage_1_result_path, thread, dfif_command_message_id): # add safetychecks
    try:
        await thread.send(f"✅inside dfif2, upscaling")  
        
        # run blocking function in executor
        loop = asyncio.get_running_loop()
        result_path = await loop.run_in_executor(None, inference2, index)

        await thread.send(f"✅upscale done")          
        with open(result_path, 'rb') as f:
            await thread.send(f'Here is the upscaled image! :) ', file=discord.File(f, 'result.png'))

        # using custom emoji that looks nicer
        emoji_guild = thread.guild  
        confirm_emoji_id = 1098629085955113011
        confirm_emoji = discord.utils.get(emoji_guild.emojis, id=confirm_emoji_id)
        
        # assuming dfif2 is always inside a thread, we can always exit the thread to find the channel with the original command,
        # which allows us to react confirm on that message.
        parent_channel = thread.parent
        dfif_command_message = await parent_channel.fetch_message(dfif_command_message_id)

        # reacting to original !deepfloydif command + using a custom emoji to do it
        await dfif_command_message.add_reaction(confirm_emoji)
        await thread.send(f"✅upscale posted")             
            #await ctx.reply('Here is the result of the second stage', file=discord.File(f, 'result.png'))
            #await ctx.message.add_reaction('✅') need to fix this

        '''
        try:
            dfif_command_message = await channel.fetch_message(dfif_command_message_id)
            await dfif_command_message.add_reaction('✅')            
        '''
            
    except Exception as e:
        print(f"Error: {e}")
        
        #await ctx.reply('An error occured in stage 2') need to fix
        #await ctx.message.add_reaction('❌')
#----------------------------------------------------------------------------------------------------------------------------
# react detector for stage 2 ❌
@bot.event
async def on_reaction_add(reaction, user):    # ctx = await bot.get_context(reaction.message)? could try later, might simplify
    try:
        #ctx = await bot.get_context(reaction.message)
        # safety checks first ❌
        thread = reaction.message.channel
        threadparentid = thread.parent.id
        
        if not user.bot: 
            if threadparentid == 1100458786826747945: # bot-test
                # 811235357663297546 =  lunarflu
                if reaction.message.attachments:
                    if user.id == reaction.message.mentions[0].id:  #  if user.id == reaction.message.mentions[0].id:           
                        # magic begins
                        await reaction.message.channel.send("✅reaction detected")
                        attachment = reaction.message.attachments[0]
                        image_name = attachment.filename # named something like: tmpgtv4qjix1111269940599738479.png
                        # remove .png first
                        partialpathmessageid = image_name[:-4] # should be tmpgtv4qjix1111269940599738479 
                        # extract partialpath, messageid
                        partialpath = partialpathmessageid[:11] # tmpgtv4qjix
                        messageid = partialpathmessageid[11:] # 1111269940599738479
                        # add /tmp/ to partialpath, save as new variable
                        fullpath = "/tmp/" + partialpath # should be /tmp/tmpgtv4qjix
                        await reaction.message.channel.send(f"✅fullpath extracted, {fullpath}")        
                        emoji = reaction.emoji
                        
                        if emoji == "1️⃣":
                            index = 0
                        elif emoji == "2️⃣":
                            index = 1
                        elif emoji == "3️⃣":
                            index = 2
                        elif emoji == "4️⃣":
                            index = 3 
                            
                        await reaction.message.channel.send(f"✅index extracted, {index}")         
                        index = index
                        stage_1_result_path = fullpath
                        thread = reaction.message.channel
                        dfif_command_message_id = messageid
                        ctx = await bot.get_context(reaction.message)
                        await reaction.message.channel.send(f"✅calling dfif2")  
                        await dfif2(index, stage_1_result_path, thread, dfif_command_message_id)
        
        '''

            if reaction.message.attachments:
                if user.id == reaction.message.mentions[0].id:  # all we care about is upscaling whatever image this is 
                    
                    # magic begins
                    attachment = reaction.message.attachments[0]
                    image_name = attachment.filename
                    # we know image_name will be something like 1tmpgtv4qjix.png
                    # remove .png first
                    indexpartialpath = image_name[:-4] # should be 1tmpgtv4qjix 
                    # extract index as an integer (dfif2 needs integer)
                    index = int(indexpartialpath[0]) - 1# should be 1
                    # extract partialpath
                    partialpath = indexpartialpath[1:] # should be tmpgtv4qjix
                    # add /tmp/ to partialpath, save as new variable
                    fullpath = "/tmp/" + partialpath # should be /tmp/tmpgtv4qjix
    
                    stage_1_result_path = fullpath
                    index = index
                    await dfif2(index, stage_1_result_path, thread)        
        
        '''

                
    except Exception as e:
        print(f"Error: {e}")
        
        #await ctx.reply('An error occured in stage 2') need to fix
        #await ctx.message.add_reaction('❌')
#---------------------------------------------------------------------------------------------------------------------------- 

    
def run_bot():
    bot.run(DISCORD_TOKEN)

threading.Thread(target=run_bot).start()

def greet(name):
    return "Hello " + name + "!"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")
demo.queue(concurrency_count=10)
demo.launch()
