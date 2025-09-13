import React, { useState, useEffect, useRef } from 'react';
import './RestaurantChatbot.css';
import { FaRobot, FaTimes, FaPaperPlane, FaSpinner, FaCog, FaLightbulb, FaBullhorn, FaChartLine, FaQuestionCircle, FaHistory, FaTrash, FaPlus, FaMagic, FaEdit, FaUtensils, FaCheck, FaRedo, FaCogs, FaBoxes, FaDollarSign, FaHeartbeat, FaCoffee, FaLeaf } from 'react-icons/fa';
import axios from 'axios';



const RestaurantChatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [intelligenceMode, setIntelligenceMode] = useState('QNA'); // Default mode changed to QNA
  const [showModeSelector, setShowModeSelector] = useState(false);
  const [showChatHistory, setShowChatHistory] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showInnovationOptions, setShowInnovationOptions] = useState(false);
  const [showManualInputForm, setShowManualInputForm] = useState(false);
  const [manualInputData, setManualInputData] = useState({
    name: '',
    description: '',
    ingredients: '',
    price: '',
    category: 'Main Course'
  });

  const messagesEndRef = useRef(null);

  const modes = {
    QNA: {
      name: 'Q&A Mode',
      description: 'Simple Question & Answer',
      icon: FaQuestionCircle,
      color: '#8b5cf6'
    },
    INNOVATION: {
      name: 'Innovation Mode',
      description: 'Creative Menu Development', 
      icon: FaLightbulb,
      color: '#10b981'
    }
  };

  // Initialize chat history from localStorage
  useEffect(() => {
    console.log('Initializing chat history...');
    const savedHistory = localStorage.getItem('chatbot-history');
    console.log('Loading saved history:', savedHistory);
    
    if (savedHistory) {
      try {
        const parsedHistory = JSON.parse(savedHistory);
        console.log('Parsed history:', parsedHistory);
        setChatHistory(parsedHistory);
        
        // Load the most recent chat if exists
        if (parsedHistory.length > 0) {
          const latestChat = parsedHistory[parsedHistory.length - 1];
          setCurrentChatId(latestChat.id);
          setMessages(latestChat.messages);
          setIntelligenceMode(latestChat.mode);
          console.log('Loaded existing chat:', latestChat.id);
        } else {
          console.log('No existing chats, creating new one');
          // Create initial chat with QNA welcome message
          const initialChat = {
            id: Date.now(),
            mode: 'QNA',
            messages: [{
              id: 1,
              text: "🍽️ Welcome to Menu Buddy! 🤖\n\nI'm your intelligent restaurant management assistant!\n\n❓ **Q&A MODE ACTIVATED** (Default)\n\nSimple Question & Answer Assistant\n\n**🚀 Powerful Functions:**\n**💬 Direct Answers**: Get straightforward responses to your restaurant questions\n**📋 Menu Information**: Quick details about dishes, ingredients, and pricing\n**🕒 Operating Details**: Hours, policies, and general restaurant information\n**🤝 Customer Service**: Friendly assistance with common inquiries\n\n**💬 Get Started:** Ask me any simple questions about your restaurant, menu, or operations\n\n💡 Switch modes anytime using the selector above for advanced Analytics, Promotion, or Innovation capabilities!",
              isUser: false,
              timestamp: new Date()
            }],
            createdAt: new Date().toISOString(),
            lastUpdated: new Date().toISOString(),
            title: 'Q&A Mode Chat'
          };
          setChatHistory([initialChat]);
          setCurrentChatId(initialChat.id);
          setMessages(initialChat.messages);
          console.log('Created initial chat:', initialChat);
        }
      } catch (error) {
        console.error('Error parsing chat history:', error);
        // Create fresh chat on error
        const errorChat = {
          id: Date.now(),
          mode: 'QNA',
          messages: [{
            id: 1,
            text: "🍽️ Welcome to Menu Buddy! 🤖\n\nI'm your intelligent restaurant management assistant!",
            isUser: false,
            timestamp: new Date()
          }],
          createdAt: new Date().toISOString(),
          lastUpdated: new Date().toISOString(),
          title: 'Q&A Mode Chat'
        };
        setChatHistory([errorChat]);
        setCurrentChatId(errorChat.id);
        setMessages(errorChat.messages);
      }
    } else {
      console.log('No saved history, creating initial chat');
      // Create initial chat with QNA welcome message
      const newChat = {
        id: Date.now(),
        mode: 'QNA',
        messages: [{
          id: 1,
          text: "🍽️ Welcome to Menu Buddy! 🤖\n\nI'm your intelligent restaurant management assistant!\n\n❓ **Q&A MODE ACTIVATED** (Default)\n\nSimple Question & Answer Assistant\n\n**🚀 Powerful Functions:**\n**💬 Direct Answers**: Get straightforward responses to your restaurant questions\n**📋 Menu Information**: Quick details about dishes, ingredients, and pricing\n**🕒 Operating Details**: Hours, policies, and general restaurant information\n**🤝 Customer Service**: Friendly assistance with common inquiries\n\n**💬 Get Started:** Ask me any simple questions about your restaurant, menu, or operations\n\n💡 Switch modes anytime using the selector above for advanced Analytics, Promotion, or Innovation capabilities!",
          isUser: false,
          timestamp: new Date()
        }],
        createdAt: new Date().toISOString(),
        lastUpdated: new Date().toISOString(),
        title: 'Q&A Mode Chat'
      };
      setChatHistory([newChat]);
      setCurrentChatId(newChat.id);
      setMessages(newChat.messages);
      console.log('Created new initial chat:', newChat);
    }
  }, []);

  // Save chat history to localStorage whenever it changes
  useEffect(() => {
    console.log('Chat history changed:', chatHistory);
    if (chatHistory.length > 0) {
      console.log('Saving to localStorage:', chatHistory);
      localStorage.setItem('chatbot-history', JSON.stringify(chatHistory));
    }
  }, [chatHistory]);

  // Update current chat in history when messages change
  useEffect(() => {
    if (currentChatId && messages.length > 0) {
      setChatHistory(prev => 
        prev.map(chat => {
          if (chat.id === currentChatId) {
            // Generate a better title based on the first user message
            let title = chat.title;
            const firstUserMessage = messages.find(msg => msg.isUser);
            if (firstUserMessage && messages.length > 1) {
              const shortTitle = firstUserMessage.text.substring(0, 30);
              title = shortTitle.length < firstUserMessage.text.length ? shortTitle + '...' : shortTitle;
            }
            return { 
              ...chat, 
              messages, 
              lastUpdated: new Date().toISOString(),
              title: title
            };
          }
          return chat;
        })
      );
    }
  }, [messages, currentChatId]);

  const createNewChat = (mode = 'QNA') => {
    console.log('createNewChat called with mode:', mode);
    console.log('modes object:', modes);
    
    const chatId = Date.now();
    const welcomeMessage = getWelcomeMessage(mode);
    
    const newChat = {
      id: chatId,
      mode: mode,
      messages: [welcomeMessage],
      createdAt: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
      title: `${modes[mode]?.name || mode} Chat`
    };
    
    console.log('Creating new chat:', newChat);
    setChatHistory(prev => {
      const updated = [...prev, newChat];
      console.log('Updated chat history:', updated);
      return updated;
    });
    setCurrentChatId(chatId);
    setMessages([welcomeMessage]);
    setIntelligenceMode(mode);
  };

  const getWelcomeMessage = (mode) => {
    const welcomeMessages = {
      'QNA': {
        id: 1,
        text: "🍽️ Welcome to Menu Buddy! 🤖\n\nI'm your intelligent restaurant management assistant!\n\n❓ **Q&A MODE ACTIVATED** (Default)\n\nSimple Question & Answer Assistant\n\n**🚀 Powerful Functions:**\n**💬 Direct Answers**: Get straightforward responses to your restaurant questions\n**📋 Menu Information**: Quick details about dishes, ingredients, and pricing\n**🕒 Operating Details**: Hours, policies, and general restaurant information\n**🤝 Customer Service**: Friendly assistance with common inquiries\n\n**💬 Get Started:** Ask me any simple questions about your restaurant, menu, or operations\n\n💡 Switch to Innovation mode anytime for creative menu development capabilities!",
        isUser: false,
        timestamp: new Date()
      },
      'INNOVATION': {
        id: 1,
        text: "🍽️ Welcome to Menu Buddy! 🤖\n\nI'm your intelligent restaurant management assistant with creative genius!\n\n💡 **INNOVATION MODE ACTIVATED**\n\nI'm here to help you create amazing new dishes and optimize your menu! Let's start with what you'd like to explore:\n\n**What would you like to do today?**\n\n💬 Simply tell me what you're looking for, such as:\n• \"I need new recipe ideas\"\n• \"Help me adapt a dish for dietary restrictions\"\n• \"Show me trending ingredients\"\n• \"I want to see the complete AI workflow demo\"\n\nI'll guide you step by step through the process!",
        isUser: false,
        timestamp: new Date(),
        type: 'innovation_welcome_simple',
        data: { mode: 'INNOVATION' }
      }
    };
    
    return welcomeMessages[mode] || welcomeMessages['QNA'];
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  // Function to convert markdown bold (**text**) to HTML
  const formatMessageText = (text) => {
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  };

  const handleModeChange = (newMode) => {
    // Auto-redirect to new chat when switching modes to prevent confusion
    if (newMode !== intelligenceMode) {
      createNewChat(newMode);
    }
    setShowModeSelector(false);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setIsTyping(true);

    try {
      const response = await axios.post('http://localhost:5001/api/chatbot/message', {
        message: inputValue,
        context: messages.slice(-5), // Send last 5 messages for context
        mode: intelligenceMode // Include current mode
      });

      // Debug logging for AI Recipe Engine
      if (response.data.type === 'ai_recipe_engine') {
        console.log('AI Recipe Engine Response:', response.data);
        console.log('Suggestions:', response.data.data?.suggestions);
        console.log('Suggestions length:', response.data.data?.suggestions?.length);
      }

      const botMessage = {
        id: Date.now() + 1,
        text: response.data.response || 'I apologize, but I encountered an issue processing your request.',
        isUser: false,
        timestamp: new Date(),
        type: response.data.type,
        data: response.data.data
      };

      setMessages(prev => [...prev, botMessage]);
      
      // Handle innovation mode UI updates
      if (response.data.data && response.data.data.ui_update) {
        handleUIUpdate(response.data.data.ui_update, response.data.data);
      }
      
    } catch (error) {
      console.error('Chatbot error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const handleUIUpdate = (updateType, data) => {
    switch (updateType) {
      case 'show_recipe_suggestions':
      case 'show_auto_apply_options':
      case 'highlight_dish_type_suggestions':
        setShowInnovationOptions(true);
        break;
      case 'show_manual_input_form':
        setShowManualInputForm(true);
        break;
      case 'show_auto_apply_progress':
        // Could add progress indicator here
        break;
      default:
        break;
    }
  };

  const handleDemoWorkflow = async () => {
    if (isLoading) return;

    const demoSteps = [
      {
        title: "🎯 AI Agent Demo: Complete Restaurant Intelligence Workflow",
        message: "Welcome to the comprehensive AI Agent demonstration! I'll showcase all advanced capabilities in sequence.",
        delay: 2000
      },
      {
        title: "📊 Step 1: Demand Forecasting",
        message: "First, let's analyze demand patterns and predict future trends...",
        command: "forecast_demand",
        delay: 3000
      },
      {
        title: "📦 Step 2: Inventory Analysis",
        message: "Now analyzing current inventory levels and optimization opportunities...",
        command: "analyze_inventory",
        delay: 3000
      },
      {
        title: "💰 Step 3: Pricing Optimization",
        message: "Optimizing pricing strategies based on market data and profitability...",
        command: "optimize_pricing",
        delay: 3000
      },
      {
        title: "🍽️ Step 4: AI Dish Creation",
        message: "Creating innovative dish suggestions using AI creativity...",
        command: "create_ai_dish",
        delay: 3000
      },
      {
        title: "🥗 Step 5: Nutrition Analysis",
        message: "Analyzing nutritional content and dietary compliance...",
        command: "nutrition_analysis",
        data: {
          dish_name: "AI-Generated Fusion Bowl",
          ingredients: ["quinoa", "grilled chicken", "avocado", "cherry tomatoes", "feta cheese"]
        },
        delay: 3000
      },
      {
        title: "🤖 Step 6: Complete Workflow Automation",
        message: "Finally, demonstrating full workflow automation for menu optimization...",
        command: "automate_workflow",
        data: "Mediterranean Fusion Bowl",
        delay: 2000
      },
      {
        title: "✅ Demo Complete!",
        message: "🎉 **AI Agent Demo Complete!**\n\nYou've seen all major capabilities:\n\n📊 **Demand Forecasting** - Predictive analytics\n📦 **Inventory Analysis** - Smart optimization\n💰 **Pricing Strategy** - Revenue maximization\n🍽️ **AI Dish Creation** - Creative innovation\n🥗 **Nutrition Analysis** - Health compliance\n🤖 **Workflow Automation** - End-to-end intelligence\n\n💡 **Ready to use any of these features individually!**",
        delay: 1000
      }
    ];

    // Add initial demo message
    const initialMessage = {
      id: Date.now(),
      text: "🚀 Starting AI Agent Demo Workflow...",
      isUser: true,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, initialMessage]);

    // Execute demo steps sequentially
    for (let i = 0; i < demoSteps.length; i++) {
      const step = demoSteps[i];
      
      await new Promise(resolve => setTimeout(resolve, step.delay));
      
      const stepMessage = {
        id: Date.now() + i,
        text: `${step.title}\n\n${step.message}`,
        isUser: false,
        timestamp: new Date(),
        type: 'demo_step'
      };
      
      setMessages(prev => [...prev, stepMessage]);
      
      // Execute AI command if specified
      if (step.command) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await handleAIAgentCommand(step.command, step.data);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
  };

  const handleAIAgentCommand = async (command, data = null) => {
    if (isLoading) return;

    // Add user message showing the command being executed
    const userMessage = {
      id: Date.now(),
      text: `🤖 Executing AI Agent Command: ${command.replace('_', ' ').toUpperCase()}`,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setIsTyping(true);

    try {
      let response;
      const baseURL = '/api/ai-agent';

      switch (command) {
        case 'create_ai_dish':
          response = await axios.post(`${baseURL}/create-dish`, {
            preferences: data || {},
            context: messages.slice(-3)
          });
          break;
        case 'automate_workflow':
          response = await axios.post(`${baseURL}/automate-workflow`, {
            dish_name: data,
            context: messages.slice(-3)
          });
          break;
        case 'forecast_demand':
          response = await axios.post(`${baseURL}/forecast-demand`, {
            context: messages.slice(-3)
          });
          break;
        case 'analyze_inventory':
          response = await axios.get(`${baseURL}/analyze-inventory`);
          break;
        case 'optimize_pricing':
          response = await axios.post(`${baseURL}/optimize-pricing`, {
            strategy: data?.strategy || 'profit_maximization',
            filters: data?.filters || {},
            context: messages.slice(-3)
          });
          break;
        case 'nutrition_analysis':
          response = await axios.post(`${baseURL}/analyze-nutrition`, {
            dish_data: {
              name: data?.dish_name || 'Custom Analysis',
              ingredients: data?.ingredients || [],
              recipe_data: data?.recipe_data || {}
            },
            context: messages.slice(-3)
          });
          break;
        case 'pricing_insights':
          response = await axios.get(`${baseURL}/pricing-insights`);
          break;
        default:
          throw new Error(`Unknown AI Agent command: ${command}`);
      }

      const botMessage = {
        id: Date.now() + 1,
        text: response.data.message || 'AI Agent command completed successfully!',
        isUser: false,
        timestamp: new Date(),
        type: 'ai_agent_result',
        data: response.data
      };

      setMessages(prev => [...prev, botMessage]);
      
      // Handle any UI updates from AI Agent responses
      if (response.data.ui_update) {
        handleUIUpdate(response.data.ui_update, response.data);
      }
      
    } catch (error) {
      console.error('AI Agent command error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: `❌ AI Agent Error: ${error.response?.data?.error || error.message || 'Failed to execute command'}`,
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  // Function to fetch available inventory ingredients
  const fetchInventoryIngredients = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/inventory/full');
      return response.data.filter(item => item.quantity > 0).sort((a, b) => b.quantity - a.quantity);
    } catch (error) {
      console.error('Error fetching inventory:', error);
      return [];
    }
  };

  // Enhanced AI Recipe Engine with inventory display
  const handleAIRecipeEngine = async () => {
    setIsLoading(true);
    
    try {
      // Send request to backend AI Recipe Engine
      const response = await fetch('/api/chatbot/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: 'AI Recipe Engine - suggest new dishes',
          mode: 'INNOVATION'
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        const aiRecipeMessage = {
          id: Date.now(),
          text: result.response,
          isUser: false,
          timestamp: new Date(),
          type: result.type,
          data: result.data
        };
        
        setMessages(prev => [...prev, aiRecipeMessage]);
      } else {
        throw new Error('Failed to get AI Recipe Engine response');
      }
    } catch (error) {
      console.error('Error in AI Recipe Engine:', error);
      const errorMessage = {
        id: Date.now(),
        text: '💡 **AI Recipe Engine**\n\nPlease specify ingredients you\'d like to use. For example:\n• \'Suggest dishes using tomatoes and cheese\'\n• \'Create a recipe with chicken and herbs\'\n• \'Recommend something with seafood and vegetables\'',
        isUser: false,
        timestamp: new Date(),
        type: 'ai_recipe_help'
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };



  const handleQuickAction = (action, data = null) => {
    let message = '';
    switch (action) {
      case 'manual_input':
        message = 'manual input';
        break;
      case 'auto_apply':
        handleAutoApplyRecipe(data);
        return;
      case 'auto_apply_suggestion':
        message = `auto apply suggestion ${data}`;
        break;
      case 'manual_apply_suggestion':
        message = `manual apply suggestion ${data}`;
        break;
      case 'regenerate_appetizer':
        message = 'regenerate appetizer';
        break;
      case 'regenerate_main':
        message = 'regenerate main course';
        break;
      case 'regenerate_dessert':
        message = 'regenerate dessert';
        break;
      case 'ai_recipe_help':
        handleAIRecipeEngine();
        return;
      // AI Agent Commands - Direct API calls
      case 'automate_workflow':
        handleAIAgentCommand('automate_workflow', data);
        return;
      case 'create_ai_dish':
        handleAIAgentCommand('create_ai_dish', data);
        return;
      case 'analyze_inventory':
        handleAIAgentCommand('analyze_inventory');
        return;
      case 'optimize_pricing':
        handleAIAgentCommand('optimize_pricing');
        return;
      case 'forecast_demand':
        handleAIAgentCommand('forecast_demand');
        return;
      case 'nutrition_analysis':
        handleAIAgentCommand('nutrition_analysis');
        return;
      case 'demo_workflow':
        handleDemoWorkflow();
        return;
      case 'workflow_details':
        message = 'show workflow details';
        break;
      case 'regenerate_dish':
        message = 'regenerate dish suggestion';
        break;
      case 'modify_dish':
        message = 'modify dish parameters';
        break;
      default:
        return;
    }
    
    setInputValue(message);
    setTimeout(() => handleSendMessage(), 100);
  };

  // Extract suggested combination from message text
  const extractSuggestedCombination = (messageText) => {
    const fusionMatch = messageText.match(/"([^"]*fusion dish)"/i);
    const medleyMatch = messageText.match(/"([^"]*medley)"/i);
    const garnishMatch = messageText.match(/"([^"]*garnish)"/i);
    
    return fusionMatch?.[1] || medleyMatch?.[1] || garnishMatch?.[1] || 'general analysis';
  };

  // Handle auto apply recipe with AI agent
  const handleAutoApplyRecipe = async (dishName) => {
    if (isLoading) return;
    
    setIsLoading(true);
    
    // Add initiation message
    const initiationMessage = {
      id: Date.now(),
      text: `🤖 **AI Agent: Auto Apply Recipe**\n\nInitiating automatic recipe application for: **${dishName || 'suggested dish'}**\n\n🔄 Analyzing recipe components...\n📊 Calculating nutritional information...\n💰 Determining optimal pricing...\n📝 Creating menu item entry...`,
      sender: 'ai',
      timestamp: new Date().toLocaleTimeString(),
      type: 'ai_agent_workflow'
    };
    
    setMessages(prev => [...prev, initiationMessage]);
    
    try {
      // Create AI agent prompt for auto apply
      const aiPrompt = `🤖 **AI AGENT: AUTO APPLY RECIPE WORKFLOW**\n\n**TASK:** Automatically create and apply a complete menu item for "${dishName || 'suggested dish'}"\n\n**REQUIRED ANALYSIS:**\n\n📋 **1. Recipe Development**\n• Create detailed recipe with ingredients and quantities\n• Specify cooking method and preparation steps\n• Determine serving size and portion specifications\n\n💰 **2. Cost & Pricing Analysis**\n• Calculate ingredient costs based on current inventory\n• Determine optimal menu price (2.5-3.5x ingredient cost)\n• Consider market positioning and competitor pricing\n\n🥗 **3. Nutritional Information**\n• Calculate calories, protein, carbs, fat per serving\n• Identify key nutritional highlights\n• Note any dietary restrictions or allergens\n\n📊 **4. Menu Categorization**\n• Assign appropriate category (Appetizer, Main Course, Dessert, etc.)\n• Determine cuisine type and style\n• Create appealing menu description\n\n**OUTPUT FORMAT:**\n\n\`\`\`json\n{\n  \"menu_item_name\": \"[Dish Name]\",\n  \"typical_ingredient_cost\": [cost_number],\n  \"menu_price\": [price_number],\n  \"category\": \"[category]\",\n  \"cuisine_type\": \"[cuisine]\",\n  \"key_ingredients_tags\": \"[comma-separated ingredients]\",\n  \"serving_size\": \"[serving size]\",\n  \"cooking_method\": \"[cooking method]\",\n  \"recipe_details\": \"[detailed recipe]\",\n  \"nutrition_info\": {\n    \"calories\": [number],\n    \"protein\": [number],\n    \"carbs\": [number],\n    \"fat\": [number]\n  }\n}\n\`\`\`\n\n**EXECUTE IMMEDIATELY** - Create complete menu item data for database insertion.`;
      
      // Send request to chatbot API
      const response = await axios.post('http://localhost:5001/api/chatbot/message', {
        message: aiPrompt
      });
      
      // Process AI response and extract menu item data
      const aiResponse = response.data.response;
      
      // Try to extract JSON from AI response
      const jsonMatch = aiResponse.match(/```json\s*([\s\S]*?)\s*```/);
      
      if (jsonMatch) {
        try {
          const menuItemData = JSON.parse(jsonMatch[1]);
          
          // Create menu item in database
          const createResponse = await axios.post('http://localhost:5001/api/menu/items', menuItemData);
          
          if (createResponse.data.success) {
            // Success message
            const successMessage = {
              id: Date.now() + 1,
              text: `✅ **Recipe Applied Successfully!**\n\n🍽️ **Menu Item Created:** ${menuItemData.menu_item_name}\n💰 **Price:** $${menuItemData.menu_price}\n📊 **Cost:** $${menuItemData.typical_ingredient_cost}\n🏷️ **Category:** ${menuItemData.category}\n🍴 **Cuisine:** ${menuItemData.cuisine_type}\n\n📝 **Recipe Details:**\n${menuItemData.recipe_details}\n\n🥗 **Nutrition (per serving):**\n• Calories: ${menuItemData.nutrition_info?.calories || 'N/A'}\n• Protein: ${menuItemData.nutrition_info?.protein || 'N/A'}g\n• Carbs: ${menuItemData.nutrition_info?.carbs || 'N/A'}g\n• Fat: ${menuItemData.nutrition_info?.fat || 'N/A'}g\n\n🎉 The menu item has been automatically added to your restaurant database!`,
              sender: 'ai',
              timestamp: new Date().toLocaleTimeString(),
              type: 'ai_agent_success'
            };
            
            setMessages(prev => [...prev, successMessage]);
          } else {
            throw new Error(createResponse.data.error || 'Failed to create menu item');
          }
        } catch (parseError) {
          throw new Error('Failed to parse AI response data');
        }
      } else {
        // Fallback: show AI response even if no JSON found
        const fallbackMessage = {
          id: Date.now() + 1,
          text: `🤖 **AI Agent Response:**\n\n${aiResponse}\n\n⚠️ **Note:** Could not automatically create menu item. Please review the analysis above and create manually if needed.`,
          sender: 'ai',
          timestamp: new Date().toLocaleTimeString(),
          type: 'ai_agent_response'
        };
        
        setMessages(prev => [...prev, fallbackMessage]);
      }
      
    } catch (error) {
      console.error('Auto apply recipe error:', error);
      
      const errorMessage = {
        id: Date.now() + 2,
        text: `❌ **Auto Apply Failed**\n\nError: ${error.message}\n\nPlease try again or apply the recipe manually.`,
        sender: 'ai',
        timestamp: new Date().toLocaleTimeString(),
        type: 'ai_agent_error'
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleWorkflowAction = async (workflowType, dishName) => {
    if (isLoading) return;
    
    let message = '';
    let workflowTitle = '';
    
    switch (workflowType) {
      case 'menu_planning':
        workflowTitle = '🍽️ Menu Planning Analysis';
        message = `🍽️ AI AGENT: Complete Menu Planning Workflow\n\nPlease create a comprehensive menu planning analysis for "${dishName}" including:\n\n1. Recipe Development:\n   - Complete ingredient list with quantities\n   - Step-by-step cooking instructions\n   - Preparation and cooking time\n\n2. Cost Analysis:\n   - Ingredient cost breakdown\n   - Labor cost estimation\n   - Suggested selling price\n\n3. Menu Integration:\n   - Category placement recommendation\n   - Pairing suggestions\n   - Seasonal availability\n\n4. Marketing Strategy:\n   - Target customer segment\n   - Promotional ideas\n   - Upselling opportunities\n\nProvide actionable recommendations and complete this menu planning process.`;
        break;
      case 'demand_forecasting':
        workflowTitle = '📊 Demand Forecasting Analysis';
        message = `📊 AI AGENT: Complete Demand Forecasting Analysis\n\nGenerate comprehensive demand forecasting for "${dishName}" including:\n\n1. Market Analysis:\n   - Target demographic assessment\n   - Seasonal demand patterns\n   - Competition analysis\n\n2. Sales Projections:\n   - Daily/weekly/monthly estimates\n   - Peak hours identification\n   - Special events impact\n\n3. Inventory Planning:\n   - Required ingredient quantities\n   - Storage requirements\n   - Supplier recommendations\n\n4. Risk Assessment:\n   - Demand volatility factors\n   - Mitigation strategies\n   - Alternative scenarios\n\nProvide specific numbers and actionable forecasting data.`;
        break;
      case 'pricing_adjustment':
        workflowTitle = '💰 Pricing Strategy Optimization';
        message = `💰 AI AGENT: Complete Pricing Strategy Optimization\n\nOptimize pricing strategy for "${dishName}" with full analysis:\n\n1. Cost Structure Analysis:\n   - Raw material costs\n   - Labor and overhead allocation\n   - Profit margin calculation\n\n2. Market Positioning:\n   - Competitor pricing comparison\n   - Value proposition assessment\n   - Price elasticity analysis\n\n3. Pricing Recommendations:\n   - Optimal price point\n   - Dynamic pricing strategies\n   - Bundle pricing options\n\n4. Revenue Optimization:\n   - Volume vs. margin trade-offs\n   - Promotional pricing tactics\n   - Long-term pricing strategy\n\nProvide specific price recommendations with justification.`;
        break;
      case 'nutrition_info':
        workflowTitle = '🥗 Nutrition Analysis';
        message = `🥗 AI AGENT: Complete Nutrition Analysis Workflow\n\nProvide comprehensive nutrition analysis for "${dishName}":\n\n1. Nutritional Breakdown:\n   - Calories per serving\n   - Macronutrients (protein, carbs, fats)\n   - Micronutrients and vitamins\n   - Allergen information\n\n2. Health Assessment:\n   - Dietary compliance (keto, vegan, etc.)\n   - Health benefits\n   - Nutritional warnings\n\n3. Optimization Suggestions:\n   - Healthier ingredient substitutions\n   - Portion size recommendations\n   - Nutritional enhancement options\n\n4. Compliance & Labeling:\n   - FDA labeling requirements\n   - Health claims validation\n   - Dietary restriction compatibility\n\nProvide detailed nutritional data and improvement recommendations.`;
        break;
      case 'automated_workflow':
        workflowTitle = '🤖 Automated Workflow Execution';
        message = `🤖 AI AGENT: Execute Complete Automated Workflow\n\nRun full automated dish creation workflow for "${dishName}":\n\n1. Recipe Creation:\n   - Generate complete recipe with ingredients and instructions\n   - Calculate nutritional information\n   - Determine cooking time and difficulty\n\n2. Business Analysis:\n   - Cost analysis and pricing recommendations\n   - Market positioning and target audience\n   - Demand forecasting and sales projections\n\n3. Operational Planning:\n   - Kitchen workflow optimization\n   - Staff training requirements\n   - Equipment and supply needs\n\n4. Implementation Strategy:\n   - Menu integration timeline\n   - Marketing and promotion plan\n   - Quality control measures\n   - Performance tracking metrics\n\nExecute this complete workflow and provide a comprehensive implementation plan ready for restaurant operations.`;
        break;
      default:
        return;
    }
    
    // Add workflow initiation message to chat
    const workflowInitMessage = {
      id: Date.now(),
      text: `Initiating ${workflowTitle} for "${dishName}"...`,
      isUser: true,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, workflowInitMessage]);
    setIsLoading(true);
    setIsTyping(true);
    
    try {
      const response = await axios.post('http://localhost:5001/api/chatbot/message', {
        message: message,
        context: messages.slice(-5),
        mode: intelligenceMode
      });
      
      const botMessage = {
        id: Date.now() + 1,
        text: response.data.response || 'I apologize, but I encountered an issue processing your workflow request.',
        isUser: false,
        timestamp: new Date(),
        type: response.data.type,
        data: response.data.data
      };
      
      setMessages(prev => [...prev, botMessage]);
      
      // Handle innovation mode UI updates
      if (response.data.data && response.data.data.ui_update) {
        handleUIUpdate(response.data.data.ui_update, response.data.data);
      }
      
    } catch (error) {
      console.error('Workflow error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: `I'm sorry, I encountered an error while processing the ${workflowTitle.toLowerCase()}. Please try again.`,
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const handleManualInputSubmit = () => {
    const formattedInput = `Name: ${manualInputData.name}\nDescription: ${manualInputData.description}\nIngredients: ${manualInputData.ingredients}\nPrice: $${manualInputData.price}\nCategory: ${manualInputData.category}`;
    
    setInputValue(formattedInput);
    setShowManualInputForm(false);
    setManualInputData({
      name: '',
      description: '',
      ingredients: '',
      price: '',
      category: 'Main Course'
    });
    
    setTimeout(() => handleSendMessage(), 100);
  };

  const handleManualInputChange = (field, value) => {
    setManualInputData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    if (currentChatId) {
      const welcomeMessage = getWelcomeMessage(intelligenceMode);
      setMessages([welcomeMessage]);
      
      // Update the current chat in history
      setChatHistory(prev => 
        prev.map(chat => 
          chat.id === currentChatId 
            ? { ...chat, messages: [welcomeMessage], lastUpdated: new Date().toISOString() }
            : chat
        )
      );
    }
    setInputValue('');
  };

  const newChat = () => {
    createNewChat(intelligenceMode);
    setInputValue('');
  };

  const loadChat = (chatId) => {
    const chat = chatHistory.find(c => c.id === chatId);
    if (chat) {
      setCurrentChatId(chatId);
      setMessages(chat.messages);
      setIntelligenceMode(chat.mode);
    }
  };

  const deleteChat = (chatId) => {
    setChatHistory(prev => prev.filter(chat => chat.id !== chatId));
    
    // If deleting current chat, create a new one
    if (chatId === currentChatId) {
      createNewChat();
    }
  };

  if (!isOpen) {
    return (
      <div className="chatbot-container">
        <button 
          className="chatbot-button" 
          onClick={toggleChat} 
          title="Restaurant Intelligence Agent"
        >
          <img 
            src="/menu-buddy-logo.svg" 
            alt="Menu Buddy" 
            className="chatbot-logo"
          />
        </button>
      </div>
    );
  }

  return (
    <div className="chatbot-container">
      <div className={`chat-window ${showChatHistory ? 'history-open' : ''}`}>
        <div className="chat-header">
          <div className="chat-header-info">
            <img 
              src="/menu-buddy-logo.svg" 
              alt="Menu Buddy" 
              className="chatbot-logo"
            />
            <div className="chat-header-text">
              <h3>Menu Buddy</h3>
              <p>Restaurant Intelligence Agent</p>
            </div>
          </div>
          
          <div className="header-controls">
            <button 
              className="header-control-button"
              onClick={() => setShowChatHistory(!showChatHistory)}
              title="Chat History"
            >
              <FaHistory />
            </button>
            
            <div className="mode-selector-container">
              <button 
                className="mode-selector-button"
                onClick={() => setShowModeSelector(!showModeSelector)}
                style={{ color: modes[intelligenceMode].color }}
                title={`Current: ${modes[intelligenceMode].name}`}
              >
                {React.createElement(modes[intelligenceMode].icon)}
                <FaCog className="mode-settings-icon" />
              </button>
              
              {showModeSelector && (
                <div className="mode-dropdown">
                  {Object.entries(modes).map(([key, mode]) => {
                    const IconComponent = mode.icon;
                    return (
                      <button
                        key={key}
                        className={`mode-option ${intelligenceMode === key ? 'active' : ''}`}
                        onClick={() => handleModeChange(key)}
                        style={{ borderLeft: `4px solid ${mode.color}` }}
                      >
                        <IconComponent style={{ color: mode.color }} />
                        <div className="mode-info">
                          <span className="mode-name">{mode.name}</span>
                          <span className="mode-description">{mode.description}</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
            
            <button className="close-button" onClick={toggleChat}>
              <FaTimes />
            </button>
          </div>
        </div>

        {showChatHistory && (
          <div className="chat-history-sidebar">
            <div className="chat-history-header">
              <h4>Chat History</h4>
              <button 
                className="new-chat-button"
                onClick={() => createNewChat(intelligenceMode)}
                title="Start New Chat"
              >
                <FaPlus />
              </button>
            </div>
            <div className="chat-history-list">
              <div style={{padding: '10px', fontSize: '12px', color: '#666'}}>
                Debug: {chatHistory.length} chats in history
              </div>
              {chatHistory.length === 0 ? (
                <div className="no-history">No chat history yet</div>
              ) : (
                chatHistory.slice().reverse().map((chat) => (
                  <div 
                    key={chat.id}
                    className={`chat-history-item ${chat.id === currentChatId ? 'active' : ''}`}
                    onClick={() => loadChat(chat.id)}
                  >
                    <div className="chat-history-info">
                      <div className="chat-title">
                        <span className="mode-indicator" style={{ color: modes[chat.mode].color }}>
                          {React.createElement(modes[chat.mode].icon)}
                        </span>
                        {chat.title}
                      </div>
                      <div className="chat-preview">
                        {chat.messages.length > 1 
                          ? chat.messages[chat.messages.length - 1].text.substring(0, 50) + '...'
                          : 'New conversation'
                        }
                      </div>
                      <div className="chat-date">
                        {new Date(chat.lastUpdated).toLocaleDateString()}
                      </div>
                    </div>
                    <button 
                      className="delete-chat-button"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteChat(chat.id);
                      }}
                      title="Delete Chat"
                    >
                      <FaTrash />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        <div className="chat-messages">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.isUser ? 'user' : 'bot'}`}>
              <div dangerouslySetInnerHTML={{ __html: formatMessageText(message.text) }} />
              
              {/* Innovation Mode Interactive Elements */}
              {!message.isUser && message.data && message.data.mode === 'INNOVATION' && (
                <div className="innovation-actions">
                  {/* AI Agent Workflow Results */}
                  {message.type === 'ai_agent_workflow' && (
                    <div className="ai-workflow-results">
                      <div className="workflow-summary">
                        <h4>🤖 AI Agent Analysis Complete</h4>
                      </div>
                      <div className="workflow-actions">
                        <button 
                          className="action-button auto-apply"
                          onClick={() => handleQuickAction('auto_apply', message.data.dish_suggestion.name)}
                        >
                          <FaCheck /> Add to Menu
                        </button>
                        <button 
                          className="action-button details"
                          onClick={() => handleQuickAction('workflow_details')}
                        >
                          <FaChartLine /> View Details
                        </button>
                        <button 
                          className="action-button regenerate"
                          onClick={() => handleQuickAction('regenerate_dish')}
                        >
                          <FaRedo /> Regenerate
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {/* AI Dish Creation Results */}
                  {message.type === 'ai_dish_creation' && (
                    <div className="ai-dish-creation">
                      <div className="dish-analysis">
                        <div className="analysis-scores">
                          <div className="score-item">
                            <span className="score-label">Creativity:</span>
                            <div className="score-bar">
                              <div 
                                className="score-fill creativity" 
                                style={{width: `${message.data.dish_suggestion.creativity_score * 100}%`}}
                              ></div>
                              <span className="score-text">{(message.data.dish_suggestion.creativity_score * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                          <div className="score-item">
                            <span className="score-label">Feasibility:</span>
                            <div className="score-bar">
                              <div 
                                className="score-fill feasibility" 
                                style={{width: `${message.data.dish_suggestion.feasibility_score * 100}%`}}
                              ></div>
                              <span className="score-text">{(message.data.dish_suggestion.feasibility_score * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                          <div className="score-item">
                            <span className="score-label">Nutrition:</span>
                            <div className="score-bar">
                              <div 
                                className="score-fill nutrition" 
                                style={{width: `${message.data.dish_suggestion.nutrition_score * 100}%`}}
                              ></div>
                              <span className="score-text">{(message.data.dish_suggestion.nutrition_score * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="dish-actions">
                        <button 
                          className="action-button workflow"
                          onClick={() => handleQuickAction('automate_workflow', message.data.dish_suggestion.name)}
                        >
                          <FaMagic /> Automate Workflow
                        </button>
                        <button 
                          className="action-button auto-apply"
                          onClick={() => handleQuickAction('auto_apply', message.data.dish_suggestion.name)}
                        >
                          <FaCheck /> Auto Apply
                        </button>
                        <button 
                          className="action-button modify"
                          onClick={() => handleQuickAction('modify_dish')}
                        >
                          <FaEdit /> Modify Dish
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {/* AI Inventory Suggestions */}
                  {message.type === 'ai_inventory_suggestions' && (
                    <div className="ai-inventory-suggestions">
                      <div className="inventory-overview">
                        <h4>📦 High Inventory Items</h4>
                        <div className="inventory-items">
                          {message.data.inventory_items.slice(0, 5).map((item, index) => (
                            <span key={index} className="inventory-tag">
                              {item.name} ({item.quantity})
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="suggestions-grid">
                        {message.data.suggestions.map((suggestion, index) => (
                          <div key={index} className="suggestion-card">
                            <h5>{suggestion.name}</h5>
                            <p className="suggestion-ingredients">{suggestion.ingredients.join(', ')}</p>
                            <div className="suggestion-metrics">
                              <span className="price">${suggestion.price}</span>
                              <span className="demand">{suggestion.demand} units/week</span>
                              <span className="score">Score: {suggestion.score.toFixed(1)}</span>
                            </div>
                            <button 
                              className="suggestion-action"
                              onClick={() => handleQuickAction('automate_workflow', suggestion.name)}
                            >
                              <FaMagic /> Analyze
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {message.type === 'ai_recipe_suggestions' && (
                    <div className="recipe-suggestion-actions">
                      <button 
                        className="action-button auto-apply"
                        onClick={() => handleQuickAction('auto_apply', 'fusion bowl')}
                      >
                        <FaMagic /> Auto Apply Recipe
                      </button>
                      <button 
                        className="action-button manual-input"
                        onClick={() => handleQuickAction('manual_input')}
                      >
                        <FaEdit /> Manual Input
                      </button>
                    </div>
                  )}
                  
                  {/* Show recipe suggestions from AI Recipe Engine */}
                  {message.type === 'ai_recipe_engine' && message.data && (
                    <div className="recipe-engine-suggestions">
                      {message.data.suggestions && message.data.suggestions.length > 0 ? (
                        <>
                          <h4>🍽️ Recipe Suggestions:</h4>
                          <div className="suggestion-buttons-grid">
                            {message.data.suggestions.map((suggestion, index) => (
                              <div key={index} className="suggestion-item">
                                <div className="suggestion-header">
                                  <FaUtensils /> <strong>{suggestion.text}</strong>
                                </div>
                                {suggestion.description && (
                                  <div className="suggestion-description">
                                    {suggestion.description}
                                  </div>
                                )}
                                <div className="workflow-options">
                                  <button 
                                    className="workflow-btn automated-workflow"
                                    onClick={() => handleWorkflowAction('automated_workflow', suggestion.text)}
                                  >
                                    🤖 Automated Workflow
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </>
                      ) : (
                        <div className="no-suggestions">
                          <h4>🤖 Automated Workflow:</h4>
                          <div className="workflow-options">
                            <button 
                              className="workflow-btn automated-workflow"
                              onClick={() => handleWorkflowAction('automated_workflow', extractSuggestedCombination(message.text))}
                            >
                              🤖 Automated Workflow
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  


                  {/* Show initial guidance buttons only for welcome message */}
                  {message.type === 'innovation_welcome_simple' && (
                    <div className="innovation-quick-actions">
                      <h4>🚀 Quick Start Options:</h4>
                      <div className="quick-action-grid">
                        <button 
                          className="quick-action-btn"
                          onClick={() => handleQuickAction('ai_recipe_help')}
                        >
                          <FaLightbulb /> New Recipe Ideas
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {/* Show detailed options only after user engages with recipe engine */}
                  {message.type === 'ai_recipe_help' && (
                    <div className="innovation-quick-actions">
                      <h4>🤖 AI Agent Commands:</h4>
                      <div className="quick-action-grid">
                        <button 
                          className="quick-action-btn"
                          onClick={() => handleQuickAction('create_ai_dish')}
                        >
                          <FaMagic /> Create AI Dish
                        </button>
                        <button 
                          className="quick-action-btn"
                          onClick={() => handleQuickAction('automate_workflow')}
                        >
                          <FaCogs /> Automate Workflow
                        </button>
                        <button 
                          className="quick-action-btn"
                          onClick={() => handleQuickAction('analyze_inventory')}
                        >
                          <FaBoxes /> Analyze Inventory
                        </button>
                      </div>
                      
                      <h4>🚀 Quick Actions:</h4>
                      <div className="quick-action-grid">
                        <button 
                          className="quick-action-btn"
                          onClick={() => handleQuickAction('manual_input')}
                        >
                          <FaEdit /> Manual Input
                        </button>
                        <button 
                          className="quick-action-btn"
                          onClick={() => handleQuickAction('auto_apply')}
                        >
                          <FaMagic /> Auto Apply
                        </button>
                      </div>
                      
                      <h4>🍽️ Dish Type Regeneration:</h4>
                      <div className="dish-type-grid">
                        <button 
                          className="dish-type-btn appetizer"
                          onClick={() => handleQuickAction('regenerate_appetizer')}
                        >
                          <FaUtensils /> Appetizers
                        </button>
                        <button 
                          className="dish-type-btn main"
                          onClick={() => handleQuickAction('regenerate_main')}
                        >
                          <FaUtensils /> Main Course
                        </button>
                        <button 
                          className="dish-type-btn dessert"
                          onClick={() => handleQuickAction('regenerate_dessert')}
                        >
                          <FaUtensils /> Desserts
                        </button>
                      </div>
                    </div>
                  )}
                  
                  {message.type === 'auto_apply_processing' && (
                    <div className="auto-apply-progress">
                      <div className="progress-indicator">
                        <FaSpinner className="fa-spin" /> Processing Auto Apply...
                      </div>
                      <button 
                        className="action-button confirm"
                        onClick={() => setInputValue('confirm auto apply')}
                      >
                        <FaCheck /> Confirm & Add to Menu
                      </button>
                    </div>
                  )}
                  
                  {message.type === 'dish_type_regeneration' && (
                    <div className="dish-regeneration-actions">
                      <button 
                        className="action-button regenerate"
                        onClick={() => handleQuickAction('auto_apply', message.data.dish_type)}
                      >
                        <FaMagic /> Auto Apply {message.data.dish_type}
                      </button>
                      <button 
                        className="action-button regenerate"
                        onClick={() => handleQuickAction('regenerate_' + message.data.dish_type.replace(' ', '_'))}
                      >
                        <FaRedo /> More {message.data.dish_type}s
                      </button>
                    </div>
                  )}
                  
                  {message.type === 'proactive_dish_suggestions' && message.data && message.data.suggestions && (
                    <div className="proactive-dish-suggestions">
                      <h4>💡 Suggested Combinations:</h4>
                      <div className="suggestions-grid">
                        {message.data.suggestions.map((suggestion, index) => (
                          <div key={index} className="suggestion-card">
                            <div className="suggestion-header">
                              <h5>{suggestion.name}</h5>
                              <span className="category-badge">{suggestion.category}</span>
                            </div>
                            <p className="suggestion-description">{suggestion.description}</p>
                            <div className="suggestion-details">
                              <div className="detail-item">
                                <span className="detail-label">🥘 Ingredients:</span>
                                <span className="detail-value">{suggestion.ingredients}</span>
                              </div>
                              <div className="detail-item">
                                <span className="detail-label">💰 Price:</span>
                                <span className="detail-value">{suggestion.estimated_price}</span>
                              </div>
                              <div className="detail-item">
                                <span className="detail-label">⏱️ Prep Time:</span>
                                <span className="detail-value">{suggestion.prep_time}</span>
                              </div>
                            </div>
                            <div className="suggestion-actions">
                              <button 
                                className="suggestion-action auto-apply"
                                onClick={() => handleQuickAction('auto_apply_suggestion', (index + 1).toString())}
                              >
                                <FaMagic /> Auto Apply
                              </button>
                              <button 
                                className="suggestion-action manual-apply"
                                onClick={() => handleQuickAction('manual_apply_suggestion', (index + 1).toString())}
                              >
                                <FaEdit /> Manual Apply
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      <div className="dish-action-grid">
                        <h5>🎯 Quick Actions:</h5>
                        <button 
                          className="dish-action-btn auto-apply"
                          onClick={() => handleQuickAction('auto_apply_suggestion', '1')}
                        >
                          <FaMagic /> Auto Apply Suggestion 1
                        </button>
                        <button 
                          className="dish-action-btn auto-apply"
                          onClick={() => handleQuickAction('auto_apply_suggestion', '2')}
                        >
                          <FaMagic /> Auto Apply Suggestion 2
                        </button>
                        <button 
                          className="dish-action-btn auto-apply"
                          onClick={() => handleQuickAction('auto_apply_suggestion', '3')}
                        >
                          <FaMagic /> Auto Apply Suggestion 3
                        </button>
                      </div>
                      
                      <div className="dish-action-grid">
                        <button 
                          className="dish-action-btn manual-apply"
                          onClick={() => handleQuickAction('manual_apply_suggestion', '1')}
                        >
                          <FaEdit /> Manual Apply Suggestion 1
                        </button>
                        <button 
                          className="dish-action-btn manual-apply"
                          onClick={() => handleQuickAction('manual_apply_suggestion', '2')}
                        >
                          <FaEdit /> Manual Apply Suggestion 2
                        </button>
                        <button 
                          className="dish-action-btn manual-apply"
                          onClick={() => handleQuickAction('manual_apply_suggestion', '3')}
                        >
                          <FaEdit /> Manual Apply Suggestion 3
                        </button>
                      </div>
                      
                      <div className="preference-actions">
                        <h5>🔄 Or Specify Your Preferences:</h5>
                        <div className="preference-grid">
                          <button 
                            className="preference-btn spicy"
                            onClick={() => setInputValue('I prefer spicy Asian dishes')}
                          >
                            🌶️ Spicy Asian
                          </button>
                          <button 
                            className="preference-btn italian"
                            onClick={() => setInputValue('I prefer Italian cuisine')}
                          >
                            🍝 Italian
                          </button>
                          <button 
                            className="preference-btn healthy"
                            onClick={() => setInputValue('I prefer healthy appetizers')}
                          >
                            🥗 Healthy
                          </button>
                          <button 
                            className="preference-btn dessert"
                            onClick={() => setInputValue('I prefer sweet desserts')}
                          >
                            🍰 Sweet Desserts
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          
          {isTyping && (
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Manual Input Form */}
        {showManualInputForm && (
          <div className="manual-input-overlay">
            <div className="manual-input-form">
              <div className="form-header">
                <h3>🍽️ Add New Menu Item</h3>
                <button 
                  className="close-form-btn"
                  onClick={() => setShowManualInputForm(false)}
                >
                  ×
                </button>
              </div>
              
              <div className="form-content">
                <div className="form-group">
                  <label>Dish Name *</label>
                  <input
                    type="text"
                    value={manualInputData.name}
                    onChange={(e) => handleManualInputChange('name', e.target.value)}
                    placeholder="Enter dish name"
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label>Description *</label>
                  <textarea
                    value={manualInputData.description}
                    onChange={(e) => handleManualInputChange('description', e.target.value)}
                    placeholder="Describe the dish"
                    rows="3"
                    required
                  />
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>Price ($) *</label>
                    <input
                      type="number"
                      value={manualInputData.price}
                      onChange={(e) => handleManualInputChange('price', e.target.value)}
                      placeholder="0.00"
                      step="0.01"
                      min="0"
                      required
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Category *</label>
                    <select
                      value={manualInputData.category}
                      onChange={(e) => handleManualInputChange('category', e.target.value)}
                      required
                    >
                      <option value="Main Course">Main Course</option>
                      <option value="Appetizer">Appetizer</option>
                      <option value="Dessert">Dessert</option>
                      <option value="Beverage">Beverage</option>
                      <option value="Side Dish">Side Dish</option>
                    </select>
                  </div>
                </div>
                
                <div className="form-group">
                  <label>Ingredients (comma-separated) *</label>
                  <input
                    type="text"
                    value={manualInputData.ingredients}
                    onChange={(e) => handleManualInputChange('ingredients', e.target.value)}
                    placeholder="tomato, cheese, basil, olive oil"
                    required
                  />
                </div>
                
                <div className="form-actions">
                  <button 
                    className="cancel-btn"
                    onClick={() => setShowManualInputForm(false)}
                  >
                    Cancel
                  </button>
                  <button 
                    className="submit-btn"
                    onClick={handleManualInputSubmit}
                    disabled={!manualInputData.name || !manualInputData.description || !manualInputData.price || !manualInputData.category || !manualInputData.ingredients}
                  >
                    <FaCheck /> Add to Menu
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="chat-input">
          <div className="chat-controls">
            <button 
              className="chat-control-button clear-chat"
              onClick={clearChat}
              title="Clear Chat"
            >
              Clear Chat
            </button>
            <button 
              className="chat-control-button new-chat"
              onClick={newChat}
              title="New Chat"
            >
              New Chat
            </button>
          </div>
          <div className="input-row">
            <div className="input-container">
              <input
                type="text"
                placeholder="Ask about menu, nutrition, pricing, or demand..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
              />
            </div>
            <button 
              className="send-button" 
              onClick={handleSendMessage} 
              disabled={isLoading || !inputValue.trim()}
            >
              {isLoading ? <FaSpinner className="fa-spin" /> : <FaPaperPlane />}
            </button>
          </div>
        </div>
      </div>
      
      <button 
        className="chatbot-button" 
        onClick={toggleChat} 
        title="Restaurant Intelligence Agent"
      >
        <img 
          src="/menu-buddy-logo.svg" 
          alt="Menu Buddy" 
          className="chatbot-logo"
        />
      </button>
    </div>
  );
};

// CSS Styles for Innovation Mode Features
const innovationStyles = `
  .innovation-actions {
    margin-top: 15px;
    padding: 15px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 12px;
    border-left: 4px solid #007bff;
  }
  
  .recipe-suggestion-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }
  
  .action-button {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .action-button.auto-apply {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
  }
  
  .action-button.manual-input {
    background: linear-gradient(135deg, #007bff 0%, #6610f2 100%);
    color: white;
  }
  
  .action-button.confirm {
    background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
    color: #212529;
  }
  
  .action-button.regenerate {
    background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
    color: white;
  }
  
  .action-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  }
  
  .innovation-quick-actions h4 {
    margin: 0 0 12px 0;
    color: #495057;
    font-size: 16px;
    font-weight: 600;
  }
  
  .quick-action-grid, .dish-type-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px;
    margin-bottom: 20px;
  }
  
  .quick-action-btn, .dish-type-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 8px;
    border: 2px solid #dee2e6;
    border-radius: 10px;
    background: white;
    color: #495057;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: center;
  }
  
  .quick-action-btn:hover {
    border-color: #007bff;
    background: #f8f9ff;
    color: #007bff;
    transform: translateY(-1px);
  }
  
  .dish-type-btn.appetizer:hover {
    border-color: #28a745;
    background: #f8fff9;
    color: #28a745;
  }
  
  .dish-type-btn.main:hover {
    border-color: #dc3545;
    background: #fff8f8;
    color: #dc3545;
  }
  
  .dish-type-btn.dessert:hover {
    border-color: #ffc107;
    background: #fffdf8;
    color: #856404;
  }

  /* Category Selection Styles */
  .category-selection {
    margin-top: 15px;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    color: white;
  }

  .category-selection h4 {
    margin: 0 0 16px 0;
    color: white;
    font-size: 18px;
    font-weight: 600;
    text-align: center;
  }

  .category-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
  }

  .category-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 14px 12px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: center;
    backdrop-filter: blur(10px);
  }

  .category-btn:hover {
    border-color: rgba(255, 255, 255, 0.6);
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  }

  .category-btn.appetizer:hover {
    background: rgba(40, 167, 69, 0.3);
    border-color: #28a745;
  }

  .category-btn.main:hover {
    background: rgba(220, 53, 69, 0.3);
    border-color: #dc3545;
  }

  .category-btn.dessert:hover {
    background: rgba(255, 193, 7, 0.3);
    border-color: #ffc107;
  }

  .category-btn.beverage:hover {
    background: rgba(23, 162, 184, 0.3);
    border-color: #17a2b8;
  }

  .category-btn.side:hover {
    background: rgba(40, 167, 69, 0.3);
    border-color: #28a745;
  }
  
  .auto-apply-progress {
    text-align: center;
    padding: 20px;
  }
  
  .progress-indicator {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-bottom: 15px;
    color: #007bff;
    font-weight: 500;
  }
  
  .manual-input-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .manual-input-form {
    background: white;
    border-radius: 16px;
    width: 90%;
    max-width: 500px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
  }
  
  .form-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #dee2e6;
    background: linear-gradient(135deg, #007bff 0%, #6610f2 100%);
    color: white;
    border-radius: 16px 16px 0 0;
  }
  
  .form-header h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }
  
  .close-form-btn {
    background: none;
    border: none;
    color: white;
    font-size: 20px;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: background 0.3s ease;
  }
  
  .close-form-btn:hover {
    background: rgba(255,255,255,0.1);
  }

  /* AI Agent Workflow Results Styles */
  .ai-workflow-results {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 15px 0;
    color: white;
  }

  .workflow-summary h4 {
    margin: 0 0 15px 0;
    font-size: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .workflow-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
  }

  .metric {
    background: rgba(255, 255, 255, 0.1);
    padding: 12px;
    border-radius: 8px;
    text-align: center;
  }

  .metric-label {
    display: block;
    font-size: 12px;
    opacity: 0.8;
    margin-bottom: 5px;
  }

  .metric-value {
    display: block;
    font-size: 18px;
    font-weight: bold;
  }

  .workflow-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  .workflow-actions .action-button {
    flex: 1;
    min-width: 120px;
    justify-content: center;
  }

  .action-button.details {
    background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
    color: white;
  }

  .action-button.workflow {
    background: linear-gradient(135deg, #6f42c1 0%, #5a2d91 100%);
    color: white;
  }

  .action-button.modify {
    background: linear-gradient(135deg, #fd7e14 0%, #e55a00 100%);
    color: white;
  }

  /* Demo Workflow Button Styles */
  .quick-action-btn.demo-workflow {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
    color: white;
    font-weight: bold;
    border: 2px solid #ff9ff3;
    box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
    animation: pulse-demo 2s infinite;
  }

  .quick-action-btn.demo-workflow:hover {
    background: linear-gradient(135deg, #ee5a24 0%, #ff6b6b 100%);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
  }

  @keyframes pulse-demo {
    0% {
      box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
    }
    50% {
      box-shadow: 0 4px 25px rgba(255, 107, 107, 0.5);
    }
    100% {
      box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
    }
  }

  /* Enhanced AI Recipe Engine Styles */
  .message.ai_recipe_engine {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-left: 4px solid #5a67d8;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    color: white;
  }

  .inventory-section {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
    border-left: 3px solid #4caf50;
  }

  .inventory-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .inventory-item:last-child {
    border-bottom: none;
  }

  .stock-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 8px;
  }

  .stock-high {
    background-color: #4caf50;
  }

  .stock-medium {
    background-color: #ff9800;
  }

  .stock-low {
    background-color: #f44336;
  }

  .suggested-combinations {
    background: rgba(76, 175, 80, 0.1);
    border-radius: 6px;
    padding: 8px;
    margin-top: 10px;
    border-left: 3px solid #4caf50;
  }

  /* AI Dish Creation Styles */
  .ai-dish-creation {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 15px 0;
    color: white;
  }

  .analysis-scores {
    margin-bottom: 20px;
  }

  .score-item {
    margin-bottom: 15px;
  }

  .score-label {
    display: block;
    font-size: 14px;
    margin-bottom: 8px;
    font-weight: 500;
  }

  .score-bar {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 10px;
    height: 20px;
    position: relative;
    overflow: hidden;
  }

  .score-fill {
    height: 100%;
    border-radius: 10px;
    transition: width 0.8s ease;
    position: relative;
  }

  .score-fill.creativity {
    background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
  }

  .score-fill.feasibility {
    background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%);
  }

  .score-fill.nutrition {
    background: linear-gradient(90deg, #fa709a 0%, #fee140 100%);
  }

  .score-text {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 12px;
    font-weight: bold;
    color: white;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
  }

  .dish-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  .dish-actions .action-button {
    flex: 1;
    min-width: 120px;
    justify-content: center;
  }

  /* AI Inventory Suggestions Styles */
  .ai-inventory-suggestions {
    background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 15px 0;
    color: white;
  }

  .inventory-overview h4 {
    margin: 0 0 15px 0;
    font-size: 16px;
  }

  .inventory-items {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 20px;
  }

  .inventory-tag {
    background: rgba(255, 255, 255, 0.2);
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
  }

  .suggestions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
  }

  .suggestion-card {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 15px;
    backdrop-filter: blur(10px);
  }

  .suggestion-card h5 {
    margin: 0 0 8px 0;
    font-size: 16px;
    font-weight: bold;
  }

  .suggestion-ingredients {
    font-size: 12px;
    opacity: 0.9;
    margin-bottom: 12px;
    line-height: 1.4;
  }

  .suggestion-metrics {
    display: flex;
    justify-content: space-between;
    margin-bottom: 12px;
    font-size: 12px;
  }

  .suggestion-metrics span {
    background: rgba(255, 255, 255, 0.2);
    padding: 4px 8px;
    border-radius: 12px;
    font-weight: 500;
  }

  .suggestion-action {
    width: 100%;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.2);
    border: none;
    border-radius: 6px;
    color: white;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
  }

  .suggestion-action:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: translateY(-2px);
  }

  .close-form-btn {
    background: none;
    border: none;
    color: white;
    font-size: 24px;
    cursor: pointer;
    padding: 0;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: background 0.3s ease;
  }
  
  .close-form-btn:hover {
    background: rgba(255,255,255,0.2);
  }
  
  .form-content {
    padding: 24px;
  }
  
  .form-group {
    margin-bottom: 20px;
  }
  
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  
  .form-group label {
    display: block;
    margin-bottom: 6px;
    color: #495057;
    font-weight: 500;
    font-size: 14px;
  }
  
  .form-group input,
  .form-group textarea,
  .form-group select {
    width: 100%;
    padding: 12px;
    border: 2px solid #dee2e6;
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.3s ease;
    box-sizing: border-box;
  }
  
  .form-group input:focus,
  .form-group textarea:focus,
  .form-group select:focus {
    outline: none;
    border-color: #007bff;
    box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
  }
  
  .form-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid #dee2e6;
  }
  
  .cancel-btn {
    padding: 12px 24px;
    border: 2px solid #6c757d;
    background: white;
    color: #6c757d;
    border-radius: 8px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .cancel-btn:hover {
    background: #6c757d;
    color: white;
  }
  
  .submit-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 24px;
    border: none;
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
    border-radius: 8px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .submit-btn:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(40,167,69,0.3);
  }
  
  .submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
  
  /* Recipe Engine Suggestions Styles */
  .recipe-engine-suggestions {
    margin-top: 20px;
    padding: 20px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    backdrop-filter: blur(10px);
  }
  
  .recipe-engine-suggestions h4 {
    margin: 0 0 16px 0;
    color: #1a202c;
    font-size: 18px;
    font-weight: 600;
  }
  
  .suggestion-buttons-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 20px;
    margin-bottom: 24px;
  }
  
  @media (max-width: 768px) {
    .suggestion-buttons-grid {
      grid-template-columns: 1fr;
      gap: 16px;
    }
  }
  
  .suggestion-item {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(15px);
    border: 2px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease;
    margin-bottom: 8px;
  }
  
  .suggestion-item:hover {
    background: rgba(255, 255, 255, 0.25);
    border: 2px solid rgba(255, 255, 255, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
  }
  
  .suggestion-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
    color: #1a202c;
    font-size: 20px;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(255, 255, 255, 0.8);
    letter-spacing: 0.5px;
  }
  
  .suggestion-description {
    color: #2d3748;
    font-size: 16px;
    line-height: 1.6;
    margin-bottom: 16px;
    font-style: normal;
    font-weight: 500;
    padding-left: 30px;
    background: rgba(255, 255, 255, 0.9);
    padding: 12px 16px;
    border-radius: 8px;
    border-left: 4px solid #4a5568;
    text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8);
  }
  
  .workflow-options {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 10px;
  }
  
  .workflow-btn {
    padding: 12px 16px;
    border: none;
    border-radius: 8px;
    color: white;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 13px;
    text-align: center;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .workflow-btn.menu-planning {
    background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
  }
  
  .workflow-btn.demand-forecasting {
    background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  }
  
  .workflow-btn.pricing-adjustment {
    background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
  }
  
  .workflow-btn.nutrition-info {
    background: linear-gradient(135deg, #9C27B0 0%, #7B1FA2 100%);
  }
  
  .workflow-btn.automated-workflow {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  }
  
  .workflow-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    opacity: 0.95;
    border: 1px solid rgba(255, 255, 255, 0.4);
  }
  
  .workflow-btn:active {
    transform: translateY(0);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }
  
  .suggestion-actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }
  
  .suggestion-actions .quick-action-btn {
    flex: 1;
    min-width: 180px;
  }
  
  .no-suggestions {
    text-align: center;
    padding: 20px;
    margin-bottom: 20px;
  }
  
  .no-suggestions h4 {
    margin: 0 0 8px 0;
    color: white;
    font-size: 16px;
  }
  
  .no-suggestions p {
    margin: 0;
    color: rgba(255, 255, 255, 0.8);
    font-size: 14px;
  }
  
  @media (max-width: 768px) {
    .form-row {
      grid-template-columns: 1fr;
    }
    
    .quick-action-grid, .dish-type-grid {
      grid-template-columns: 1fr;
    }
    
    .recipe-suggestion-actions {
      flex-direction: column;
    }
    
    .manual-input-form {
      width: 95%;
      margin: 20px;
    }
    
    .suggestion-buttons-grid {
      grid-template-columns: 1fr;
    }
    
    .suggestion-actions {
      flex-direction: column;
    }
    
    .suggestion-actions .quick-action-btn {
      min-width: auto;
    }
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = innovationStyles;
  document.head.appendChild(styleElement);
}

export default RestaurantChatbot;